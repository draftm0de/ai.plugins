#!/usr/bin/env python3
"""Inspect skill sources and scaffold/validate evidence-based GitHub documentation.

This helper never generates factual claims or executes the input skill.
"""
import argparse
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
from urllib.parse import unquote, urlsplit

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / 'templates'


def strict_json(text):
    """Reject ambiguous or non-round-trippable JSON before planning writes."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field: ' + key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Invalid JSON numeric constant: ' + value)
    def finite_number(value):
        import math
        from decimal import Decimal
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Invalid JSON numeric constant: ' + value)
        if Decimal(value) != Decimal(str(number)):
            raise ValueError('Unsupported JSON numeric precision: ' + value)
        return number
    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant, parse_float=finite_number)


def outline():
    return strict_json((TEMPLATES / 'outline.json').read_text(encoding='utf-8'))


def check_policy(policy):
    if not isinstance(policy, dict) or set(policy) != {'languages', 'default_language'}:
        raise ValueError('documentation requires languages and default_language')
    languages = policy['languages']
    if (not isinstance(languages, list) or not languages or any(x not in ('de', 'en') for x in languages)
            or len(set(languages)) != len(languages) or policy['default_language'] not in languages):
        raise ValueError('Select unique languages from de/en and a default_language in that selection')
    return policy


def language_policy(root, languages=None, default_language=None):
    manifest = read_manifest(root)
    saved = manifest.get('documentation') if manifest else None
    if languages is None:
        if default_language is not None:
            raise ValueError('default_language requires languages')
        if saved:
            return check_policy(saved)
        raise ValueError('Choose documentation languages for this repository; use --languages or docs/documentation.json documentation settings')
    requested = check_policy({'languages': list(languages), 'default_language': default_language or (languages[0] if languages else None)})
    if saved and saved != requested:
        raise ValueError('Language selection conflicts with docs/documentation.json; review the repository policy first')
    return requested


def page_layout(policy):
    pages = {}
    default = policy['default_language']
    for template, headings in outline().items():
        language = 'en' if template == 'README.en.md' or template.startswith('docs/en/') else 'de'
        if language not in policy['languages']:
            continue
        name = ('README.md' if language == default else f'README.{language}.md') if template.startswith('README') else template
        pages[name] = (template, headings, language)
    return pages


def template_text(template, policy, base=None):
    text = ((base or TEMPLATES) / template).read_text(encoding='utf-8')
    if len(policy['languages']) == 1:
        text = '\n'.join(line for line in text.split('\n') if not ('Deutsch' in line and 'English' in line and ' | ' in line))
    if policy['default_language'] == 'en':
        # Rewrite only root README links; localized guide filenames remain stable.
        text = text.replace('(README.en.md)', '(__EN_ROOT__)').replace('(README.md)', '(README.de.md)') if template.startswith('README') else text.replace('(../../README.en.md)', '(../../__EN_ROOT__)').replace('(../../README.md)', '(../../README.de.md)')
        text = text.replace('__EN_ROOT__', 'README.md')
    return text


def read_manifest(root):
    path = root / 'docs/documentation.json'
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink():
        raise ValueError('Documentation manifest must not be a symlink')
    data = strict_json(path.read_text(encoding='utf-8'))
    allowed = {'schema_version', 'source_skill', 'extra_sources', 'open_questions', 'documentation'}
    if not isinstance(data, dict) or set(data) - allowed or type(data.get('schema_version')) is not int or data.get('schema_version') != 1:
        raise ValueError('Invalid documentation manifest; store source pointers, not duplicated product facts')
    if 'documentation' not in data:
        raise ValueError('Missing explicit documentation language policy; unsupported manifest, no automatic inference or migration')
    check_policy(data['documentation'])
    if 'source_skill' in data and (not isinstance(data['source_skill'], str) or not data['source_skill']):
        raise ValueError('Invalid source_skill')
    if 'source_skill' not in data and 'documentation' not in data:
        raise ValueError('Manifest requires source_skill or documentation policy')
    for key in ('extra_sources', 'open_questions'):
        if not isinstance(data.get(key, []), list) or not all(isinstance(value, str) for value in data.get(key, [])):
            raise ValueError(f'Manifest {key} must be a list of strings')
    for value in ([data['source_skill']] if 'source_skill' in data else []) + data.get('extra_sources', []):
        target = (root / value).resolve()
        if Path(value).is_absolute() or not target.is_relative_to(root.resolve()) or not target.exists():
            raise ValueError(f'Manifest source pointer is missing or outside the repository: {value}')
    if 'source_skill' in data:
        parts = Path(data['source_skill']).parts
        target = root
        if not parts or parts[0] != 'skills' or '..' in parts:
            raise ValueError('Unsupported source layout: repository skills must be under skills/')
        for part in parts:
            target /= part
            if target.is_symlink():
                raise ValueError('Unsupported source layout: symlink source pointer')
        if not target.resolve().is_relative_to((root/'skills').resolve()):
            raise ValueError('Unsupported source layout: source escapes skills/')
    if 'source_skill' in data and not ((root / data['source_skill']) / 'SKILL.md').is_file():
        raise ValueError('Manifest source_skill has no SKILL.md; resolve the source before documenting')
    return data


def source_skill(source):
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise ValueError('Source must be an accessible local directory')
    if any((root / old).exists() or (root / old).is_symlink() for old in ('.claude/skills', '.agents/skills')):
        raise ValueError('Unsupported source layout: repository skills must be under skills/')
    manifest = read_manifest(root)
    if (root / 'SKILL.md').is_file():
        if any((root / name).exists() for name in ('plugin.json', 'marketplace.json')):
            raise ValueError('Unsupported root SKILL.md in product repository; use skills/')
        if (root / 'SKILL.md').read_text(encoding='utf-8').startswith('---\n'):
            return root
        raise ValueError('Unsupported root SKILL.md pointer; select a current skill directory')
    if manifest and 'source_skill' in manifest:
        return (root / manifest['source_skill']).resolve()
    candidates = []
    for relative in ('skills',):
        for path in sorted((root / relative).glob('*/SKILL.md')):
            resolved = path.parent.resolve()
            if resolved not in candidates:
                candidates.append(resolved)
    if len(candidates) != 1:
        raise ValueError('Select one skill directory. Candidates: ' + ', '.join(map(str, candidates)))
    return candidates[0]


def inspect(source):
    skill = source_skill(source)
    text = (skill / 'SKILL.md').read_text(encoding='utf-8')
    match = re.search(r'^name:\s*(.+)$', text, re.MULTILINE)
    evidence = ['SKILL.md']
    for folder in ('references', 'scripts'):
        for path in sorted((skill / folder).rglob('*')):
            relative = path.relative_to(skill)
            if (path.is_file() and not path.is_symlink()
                    and not any(part.startswith('.') or part == '__pycache__' for part in relative.parts)
                    and path.suffix in ('.md', '.py', '.sh', '.json', '.yaml', '.yml')):
                evidence.append(str(relative))
    return {'skill': str(skill), 'name': match.group(1).strip('"\'') if match else skill.name,
            'evidence_files': evidence, 'source_executed': False}


def icon_source():
    bundled = SKILL / 'assets/icon.png'
    if bundled.is_file():
        return bundled
    # Source checkout has one canonical brand asset; packages inject a local copy.
    source = SKILL.parents[1] / 'assets/icon.png'
    if not source.is_file():
        raise ValueError('Bundled icon is missing; rebuild the plugin')
    return source


def safe_target(root, relative):
    path = root
    for part in Path(relative).parts:
        if part in ('..', '/'):
            raise ValueError('Unsafe output path')
        path /= part
        if path.is_symlink():
            raise ValueError(f'Output path must not be a symlink: {path}')
    return path


def scaffold(source, output, title=None, languages=None, default_language=None):
    info = inspect(source)
    root = Path(output).expanduser().resolve()
    if root.is_relative_to(Path(info['skill'])):
        raise ValueError('Write documentation outside the distributable source skill')
    plans = []
    manifest_path = safe_target(root, 'docs/documentation.json')
    manifest = read_manifest(root)
    policy = language_policy(root, languages, default_language)
    if manifest and 'source_skill' in manifest and (root / manifest['source_skill']).resolve() != Path(info['skill']):
        raise ValueError('Output manifest points to another skill; resolve this conflict before writing')
    if not manifest:
        manifest = {'schema_version': 1, 'extra_sources': [], 'open_questions': [], 'documentation': policy}
        if Path(info['skill']).is_relative_to(root):
            pointer = Path(info['skill']).relative_to(root)
            if not pointer.parts or pointer.parts[0] != 'skills' or '..' in pointer.parts:
                raise ValueError('Unsupported source layout: repository skills must be under skills/')
            manifest['source_skill'] = str(pointer)
        plans.append((manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()))
    for name, (template, _, _) in page_layout(policy).items():
        target = safe_target(root, name)
        if target.exists() and not target.is_file():
            raise ValueError(f'Expected a file: {target}')
        if not target.exists():
            text = template_text(template, policy)
            text = text.replace('{{TITLE}}', title or info['name'])
            plans.append((target, text.encode('utf-8')))
    icon = safe_target(root, 'docs/assets/zyris-icon.png')
    data = icon_source().read_bytes()
    if icon.exists() and (not icon.is_file() or icon.read_bytes() != data):
        raise ValueError('Existing docs/assets/zyris-icon.png differs; preserve/review it before replacing')
    if not icon.exists():
        plans.append((icon, data))
    for target, content in plans:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(content)
    return {'created': [str(p.relative_to(root)) for p, _ in plans],
            'existing_pages_preserved': True,
            'next': 'Author evidence-based content, replace placeholders, then validate. Scaffold is not finished documentation.'}


def slug(text):
    text = re.sub(r'<[^>]*>', '', text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'\s', '-', text)


def anchors(path):
    result = set()
    seen = {}
    inside = False
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('```'):
            inside = not inside
        if not inside and re.match(r'^#{1,6} ', line):
            base = slug(line.split(' ', 1)[1])
            count = seen.get(base, 0)
            seen[base] = count + 1
            result.add(base if count == 0 else f'{base}-{count}')
    return result


def validate(output):
    root = Path(output).expanduser().resolve()
    errors = []
    try:
        policy = language_policy(root)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    pages = page_layout(policy)
    for name, (_, required, language) in pages.items():
        path = safe_target(root, name)
        if not path.is_file():
            errors.append(f'{name}: missing page')
            continue
        text = path.read_text(encoding='utf-8')
        if re.search(r'\{\{[^}]+\}\}', text):
            errors.append(f'{name}: unresolved template placeholders')
        if text.count('```') % 2:
            errors.append(f'{name}: unclosed fenced block')
        prose = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        headings = re.findall(r'^## (.+)$', prose, re.MULTILINE)
        if headings != required:
            errors.append(f'{name}: level-two headings must match outline order')
        if len(re.findall(r'^# ', prose, re.MULTILINE)) != 1:
            errors.append(f'{name}: expected exactly one page title')
        if re.search(r'(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\Users\\)', text):
            errors.append(f'{name}: machine-specific path')
        if len(policy['languages']) > 1:
            other = 'en' if language == 'de' else 'de'
            if name.startswith('README'):
                counterpart = 'README.md' if other == policy['default_language'] else f'README.{other}.md'
            else:
                counterpart = '../' + other + '/' + path.name
            if f']({counterpart})' not in prose:
                errors.append(f'{name}: missing language counterpart link')
        links = re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)', prose)
        links += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', prose)
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not destination.is_relative_to(root):
                errors.append(f'{name}: link escapes repository: {link}')
                continue
            if not destination.exists():
                errors.append(f'{name}: missing link target: {link}')
            elif parsed.fragment and destination.suffix == '.md' and unquote(parsed.fragment) not in anchors(destination):
                errors.append(f'{name}: missing heading anchor: {link}')
            if '.tmp' in destination.relative_to(root).parts:
                errors.append(f'{name}: public link to ignored test artifacts')
    icon = safe_target(root, 'docs/assets/zyris-icon.png')
    if not icon.is_file() or icon.read_bytes() != icon_source().read_bytes():
        errors.append('Brand icon missing or differs from the bundled source')
    for name in (name for name in pages if name.startswith('README') or name.endswith('/README.md')):
        path = safe_target(root, name)
        if path.is_file() and 'zyris-icon.png' not in path.read_text(encoding='utf-8'):
            errors.append(f'{name}: brand icon must be referenced')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    scan = sub.add_parser('inspect')
    scan.add_argument('--source', type=Path, required=True)
    create = sub.add_parser('scaffold')
    create.add_argument('--source', type=Path, required=True)
    create.add_argument('--output', type=Path, required=True)
    create.add_argument('--title')
    create.add_argument('--languages', nargs='+', choices=('de','en'))
    create.add_argument('--default-language', choices=('de','en'))
    verify = sub.add_parser('validate')
    verify.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect':
            result = inspect(args.source)
        elif args.command == 'scaffold':
            result = scaffold(args.source, args.output, args.title, args.languages, args.default_language)
        else:
            errors = validate(args.output)
            result = {'valid': not errors, 'errors': errors,
                      'scope': 'Structure, branding and local links only; content and host claims require review.'}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return int(bool(errors))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
