"""Explicit creation-time licensing; never infer rights holders or legal terms."""
from pathlib import Path
import re

TEMPLATES = Path(__file__).resolve().parents[1] / 'templates/licenses'


def plan(root, license_id, license_file, copyright_year, copyright_holder):
    if not isinstance(license_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+-]*', license_id):
        raise ValueError('Explicit --license identifier or --license deferred is required')
    existing = [root/name for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt')
                if (root/name).exists() or (root/name).is_symlink()]
    if license_id == 'deferred':
        if existing or license_file or copyright_year or copyright_holder:
            raise ValueError('Deferred license conflicts with existing license or supplied licensing inputs')
        return {'status': 'deferred', 'identifier': None, 'file': None, 'content': None}
    if license_file:
        path = Path(license_file).absolute()
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
            raise ValueError('License source must be an explicit regular file without symlinks')
        if any(p in {'.git', '.local', '.aws', '.ssh', 'node_modules', '.venv'} or p.startswith('.env') for p in path.parts) or path.suffix in {'.pem', '.key'}:
            raise ValueError('Private or generated paths are not license sources')
        if copyright_year or copyright_holder:
            raise ValueError('Complete license file and template copyright inputs are mutually exclusive')
        content = path.read_bytes()
        text = content.decode('utf-8')
        if not text.strip() or re.search(r'\{\{.*?\}\}|<YEAR>|<COPYRIGHT HOLDER>|\[year\]|\[fullname\]', text, re.I):
            raise ValueError('License source must contain complete confirmed text without placeholders')
    elif license_id == 'MIT':
        if not isinstance(copyright_year, str) or not re.fullmatch(r'\d{4}(?:-\d{4})?', copyright_year):
            raise ValueError('MIT requires confirmed --copyright-year (YYYY or YYYY-YYYY)')
        if (not isinstance(copyright_holder, str) or not copyright_holder.strip()
                or any(ord(c) < 32 for c in copyright_holder) or any(c in copyright_holder for c in '{}<>')):
            raise ValueError('MIT requires a confirmed single-line --copyright-holder')
        content = (TEMPLATES/'MIT.txt').read_text().replace('{{YEAR}}', copyright_year).replace('{{HOLDER}}', copyright_holder).encode()
    else:
        raise ValueError('Unsupported license template; supply a confirmed complete --license-file with --license')
    if len(existing) > 1:
        raise ValueError('Multiple existing license files require explicit review before creation')
    for path in existing:
        if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
            raise ValueError('Existing license differs; preserve it and resolve the conflict before creation')
    return {'status': 'implemented', 'identifier': license_id,
            'file': existing[0].name if existing else 'LICENSE', 'content': content}


def document(stage, decision):
    """Write decision once and link it from all newly generated localized READMEs."""
    from documentation import language_policy, page_layout
    selected = decision['identifier']
    if selected:
        lines = [f'# License / Lizenz\n\n{selected}: [License text / Lizenztext](../{decision["file"]}).',
                 'The selected license file is present. / Die gewählte Lizenzdatei ist vorhanden.']
    else:
        lines = ['# License / Lizenz',
                 'The licensing decision was explicitly deferred; no license is granted by this scaffold. / '
                 'Die Lizenzentscheidung wurde ausdrücklich vertagt; dieses Gerüst erteilt keine Lizenz.']
    (stage/'docs/license.md').write_text('\n\n'.join(lines) + '\n')
    for relative, (_, _, language) in page_layout(language_policy(stage)).items():
        if not relative.startswith('README') and not relative.endswith('/README.md'):
            continue
        path = stage/relative
        text = path.read_text()
        link = 'docs/license.md' if relative.startswith('README') else '../license.md'
        sentence = (f'Lizenz: {selected or "ausdrücklich vertagt"}. Siehe [Lizenzentscheidung]({link}).'
                    if language == 'de' else
                    f'License: {selected or "explicitly deferred"}. See [licensing decision]({link}).')
        text = text.replace('Die Lizenz ist separat zu klären; erzeugte Dokumentation legt keine Lizenz fest. ', '')
        text = text.replace('Licensing must be resolved separately; generated documentation does not establish a license. ', '')
        text = text.replace('\n## ', '\n' + sentence + '\n\n## ', 1)
        path.write_text(text)


def check(root, decision):
    from documentation import language_policy, page_layout
    import json
    errors = []
    for name in ('plugin.json', '.claude-plugin/plugin.json'):
        if json.loads((root/name).read_text()).get('license') != decision['identifier']:
            errors.append(name + ': license metadata differs')
    if decision['file']:
        target = root/decision['file']
        if not target.is_file() or target.is_symlink() or target.read_bytes() != decision['content']:
            errors.append('Selected license file missing or changed')
    elif any((root/name).exists() for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt')):
        errors.append('Deferred decision conflicts with an existing license file')
    record = root/'docs/license.md'
    if not record.is_file() or record.is_symlink():
        errors.append('Persistent licensing decision missing')
    else:
        text = record.read_text()
        expected = (f'{decision["identifier"]}: [License text / Lizenztext](../{decision["file"]})'
                    if decision['identifier'] else 'The licensing decision was explicitly deferred')
        if expected not in text:
            errors.append('Persistent licensing decision differs')
    for relative in page_layout(language_policy(root)):
        if relative.startswith('README') or relative.endswith('/README.md'):
            text = (root/relative).read_text()
            if ('license.md)' not in text or
                    (decision['identifier'] and decision['identifier'] not in text)):
                errors.append(relative + ': licensing decision link missing; preserve and update existing prose')
    return {'status': decision['status'], 'identifier': decision['identifier'],
            'file': decision['file'], 'valid': not errors, 'errors': errors}
