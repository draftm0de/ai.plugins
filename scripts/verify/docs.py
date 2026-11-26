#!/usr/bin/env python3
"""Documentation check (R34, R37): pages, headings and local links; findings are warnings. Read-only.
Usage: python3 -B scripts/verify/docs.py --source <repository>. Managed by the plugin manager: do not edit."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


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


KINDS = ('plugin', 'marketplace')
# the documentation structure of both kinds: pages and their level-two headings in order
OUTLINE = {'plugin': {'README.md': ['Schnellstart', 'Features'],
            'README.en.md': ['Quick start', 'Features'],
            'docs/de/installation.md': ['Claude', 'Codex', 'Aktualisieren', 'Entfernen'],
            'docs/de/skills.md': ['📖 Skills'],
            'docs/de/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
        'docs/de/development.md': ['Voraussetzungen', 'Einrichten', 'Lokal testen', 'Befehle', 'CI', 'Gemeinsame Dateien', 'Veröffentlichen'],
            'docs/de/files.md': ['Sync-Dateien', 'Seed-Dateien', 'Wer ist wofür zuständig', 'Eine Sync-Datei ändern', 'Zurück in den Sync', 'Wenn eine Vorlage entfällt', 'Dateien und Ordner eines Plugins', 'Dateien und Ordner eines Marketplace'],
            'docs/en/installation.md': ['Claude', 'Codex', 'Update', 'Remove'],
            'docs/en/skills.md': ['📖 Skills'],
            'docs/en/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
        'docs/en/development.md': ['Requirements', 'Set up', 'Test locally', 'Commands', 'CI', 'Shared files', 'Publish'],
            'docs/en/files.md': ['Synced files', 'Seed files', 'Who is responsible for what', 'Changing a synced file', 'Back into the sync', 'When a template is removed', 'Files and folders of a plugin', 'Files and folders of a marketplace']},
 'marketplace': {'README.md': ['Plugins'],
                 'README.en.md': ['Plugins'],
                 'docs/de/installation.md': ['Claude', 'Codex', 'Aktualisieren', 'Entfernen'],
                 'docs/de/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
                 'docs/de/development.md': ['Voraussetzungen', 'Einrichten', 'Lokal testen', 'Befehle', 'CI', 'Veröffentlichen'],
                 'docs/en/installation.md': ['Claude', 'Codex', 'Update', 'Remove'],
                 'docs/en/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
                 'docs/en/development.md': ['Requirements', 'Set up', 'Test locally', 'Commands', 'CI', 'Publish']}}
SECTION_LABELS = {'de': ('Beschreibung', 'Ablauf', 'Beispiel', 'Liest und schreibt'),
                  'en': ('Description', 'Workflow', 'Example', 'Reads and writes')}
# pages of the former structure: reported, never converted or deleted
# generated pages: every heading of level 1 to 3, one to one and in this order (R46)
EXACT_HEADINGS = {
    'plugin': {
        'docs/de/installation.md': ['# ⚡ Installation', '## Claude', '### Claude Desktop App', '### Claude CLI', '## Codex', '### ChatGPT Desktop App', '### Codex CLI', '### ChatGPT Workspace', '## Aktualisieren', '## Entfernen'],
        'docs/de/concepts.md': ['# 💡 Begriffe', '## Marketplace', '## Plugin', '## Skill', '### Ein Beispiel'],
        'docs/de/development.md': ['# Entwicklung', '## Voraussetzungen', '## Einrichten', '### Marketplace', '### Plugin', '### Anforderungen und Skills', '## Lokal testen', '## Befehle', '## CI', '## Gemeinsame Dateien', '## Veröffentlichen'],
        'docs/de/files.md': ['# Gemeinsame Dateien', '## Sync-Dateien', '## Seed-Dateien', '## Wer ist wofür zuständig', '## Eine Sync-Datei ändern', '## Zurück in den Sync', '## Wenn eine Vorlage entfällt', '## Dateien und Ordner eines Plugins', '### Sync', '### Seed', '## Dateien und Ordner eines Marketplace', '### Sync', '### Seed'],
        'docs/en/installation.md': ['# ⚡ Installation', '## Claude', '### Claude Desktop App', '### Claude CLI', '## Codex', '### ChatGPT Desktop App', '### Codex CLI', '### ChatGPT Workspace', '## Update', '## Remove'],
        'docs/en/concepts.md': ['# 💡 Concepts', '## Marketplace', '## Plugin', '## Skill', '### An example'],
        'docs/en/development.md': ['# Development', '## Requirements', '## Set up', '### Marketplace', '### Plugin', '### Requirements and skills', '## Test locally', '## Commands', '## CI', '## Shared files', '## Publish'],
        'docs/en/files.md': ['# Shared files', '## Synced files', '## Seed files', '## Who is responsible for what', '## Changing a synced file', '## Back into the sync', '## When a template is removed', '## Files and folders of a plugin', '### Synced', '### Seed', '## Files and folders of a marketplace', '### Synced', '### Seed'],
    },
    'marketplace': {
        'docs/de/installation.md': ['# ⚡ Installation', '## Claude', '### Claude Desktop App', '### Claude CLI', '## Codex', '### ChatGPT Desktop App', '### Codex CLI', '### ChatGPT Workspace', '## Aktualisieren', '## Entfernen'],
        'docs/de/concepts.md': ['# 💡 Begriffe', '## Marketplace', '## Plugin', '## Skill', '### Ein Beispiel'],
        'docs/de/development.md': ['# Entwicklung', '## Voraussetzungen', '## Einrichten', '### Marketplace', '### Plugins aufnehmen', '## Lokal testen', '## Befehle', '## CI', '## Veröffentlichen'],
        'docs/en/installation.md': ['# ⚡ Installation', '## Claude', '### Claude Desktop App', '### Claude CLI', '## Codex', '### ChatGPT Desktop App', '### Codex CLI', '### ChatGPT Workspace', '## Update', '## Remove'],
        'docs/en/concepts.md': ['# 💡 Concepts', '## Marketplace', '## Plugin', '## Skill', '### An example'],
        'docs/en/development.md': ['# Development', '## Requirements', '## Set up', '### Marketplace', '### Adding plugins', '## Test locally', '## Commands', '## CI', '## Publish'],
    },
}
FEATURE_LIMIT = 200  # characters of the short explanation of one skill in the start page of a plugin
FORMER_PAGES = ('README.md', 'usage.md', 'screens.md', 'faq.md', 'storage.md')


def outline(kind='plugin'):
    return OUTLINE[kind]


def kind_of(root):
    root = Path(root)
    return 'marketplace' if (root / 'marketplace.json').is_file() and not (root / 'plugin.json').is_file() else 'plugin'


def safe_target(root, relative):
    path = root
    for part in Path(relative).parts:
        if part in ('..', '/'):
            raise ValueError('Unsafe output path')
        path /= part
        if path.is_symlink():
            raise ValueError(f'Output path must not be a symlink: {path}')
    return path


def check_policy(policy):
    if not isinstance(policy, dict) or set(policy) != {'languages', 'default_language'}:
        raise ValueError('documentation requires languages and default_language')
    languages = policy['languages']
    if (not isinstance(languages, list) or not languages or any(x not in ('de', 'en') for x in languages)
            or len(set(languages)) != len(languages) or policy['default_language'] not in languages):
        raise ValueError('Select unique languages from de/en and a default_language in that selection')
    return policy


def repository_address(url):
    """https://github.com/<owner>/<name> for a GitHub address in any common form, else None."""
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?', str(url or '').strip())
    return 'https://github.com/' + match.group(1) + '/' + match.group(2) if match else None


def read_manifest(root):
    path = root / 'docs/documentation.json'
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink():
        raise ValueError('Documentation manifest must not be a symlink')
    data = strict_json(path.read_text(encoding='utf-8'))
    allowed = {'schema_version', 'extra_sources', 'open_questions', 'documentation', 'marketplace_url'}
    if isinstance(data, dict) and 'source_skill' in data:
        raise ValueError('Unsupported field source_skill in the documentation manifest: the documentation reads every skill of the repository. Remove the field; nothing is converted automatically.')
    if not isinstance(data, dict) or set(data) - allowed or type(data.get('schema_version')) is not int or data.get('schema_version') != 1:
        raise ValueError('Invalid documentation manifest; store source pointers, not duplicated product facts')
    if 'marketplace_url' in data and repository_address(data['marketplace_url']) != data['marketplace_url']:
        raise ValueError('marketplace_url must be a plain https://github.com/<owner>/<name> address')
    if 'documentation' not in data:
        raise ValueError('Missing explicit documentation language policy; unsupported manifest, no automatic inference or migration')
    check_policy(data['documentation'])
    for key in ('extra_sources', 'open_questions'):
        if not isinstance(data.get(key, []), list) or not all(isinstance(value, str) for value in data.get(key, [])):
            raise ValueError(f'Manifest {key} must be a list of strings')
    for value in data.get('extra_sources', []):
        target = (root / value).resolve()
        if Path(value).is_absolute() or not target.is_relative_to(root.resolve()) or not target.exists():
            raise ValueError(f'Manifest source pointer is missing or outside the repository: {value}')
    return data


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


def page_layout(policy, kind='plugin'):
    pages = {}
    default = policy['default_language']
    for template, headings in outline(kind).items():
        language = 'en' if template == 'README.en.md' or template.startswith('docs/en/') else 'de'
        if language not in policy['languages']:
            continue
        name = ('README.md' if language == default else f'README.{language}.md') if template.startswith('README') else template
        pages[name] = (template, headings, language)
    return pages


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


def skill_name(path):
    """The name of a skill from its frontmatter, else its folder."""
    text = path.read_text(encoding='utf-8')
    front = text.split('---', 2)[1] if text.startswith('---') and text.count('---') >= 2 else ''
    found = re.search(r'^name:\s*(.+)$', front, re.MULTILINE)
    return found.group(1).strip().strip('"\'') if found else path.parent.name


def feature_errors(name, prose, skills, language):
    """The start page of a plugin: one `### :<skill>` entry per skill under Features, short and linked to its description."""
    section = re.split(r'^## (?:[^\w\n]+ )?Features$', prose, flags=re.MULTILINE)
    if len(section) != 2:
        return []  # a missing section is already reported by the heading order
    body = re.split(r'^## ', section[1], flags=re.MULTILINE)[0]
    parts = re.split(r'^### (.+)$', body, flags=re.MULTILINE)
    entries = dict(zip((title.strip() for title in parts[1::2]), parts[2::2]))
    errors = [f'{name}: Features lacks the entry ### :{skill}' for skill in skills if ':' + skill not in entries]
    errors += [f'{name}: Features names {title}, which is no skill of the plugin' for title in entries if title[1:] not in skills or title[:1] != ':']
    for skill in skills:
        text = entries.get(':' + skill)
        if text is None:
            continue
        if f'](docs/{language}/skills/{skill}.md)' not in text:
            errors.append(f'{name}: the feature :{skill} needs a link to docs/{language}/skills/{skill}.md')
        lines = [line for line in text.split('\n') if line.strip() and not re.fullmatch(r'\W*\[[^\]]*\]\([^)]*\)\s*', line)]
        length = len(' '.join(line.strip() for line in lines))
        if not length:
            errors.append(f'{name}: the feature :{skill} has no explanation')
        elif length > FEATURE_LIMIT:
            errors.append(f'{name}: the explanation of :{skill} has {length} characters, at most {FEATURE_LIMIT}')
    return errors


# what belongs into the sections a person writes; named when a section is still empty
HINTS = {'intro': 'what the plugin is and what you can do with it, in a few sentences',
         'quick': 'how to install and start, in a few steps',
         'feature': 'what the skill does for the person, at most %d characters' % FEATURE_LIMIT,
         0: 'what the skill does, in plain words (shown in skills.md)', 1: 'the steps in their order',
         2: 'one fictional example of a call or request', 3: 'which files and data the skill reads and what it changes'}


def open_sections(name, prose, language):
    """The sections of a hand-written page that still hold a placeholder, each with what belongs there."""
    result = []
    parts = re.split(r'(?m)^(##+ .+)$', prose)
    for index in range(0, len(parts), 2):
        heading = parts[index - 1].lstrip('# ').strip() if index else ''
        if not re.search(r'\{\{[^}]+\}\}', parts[index]):
            continue
        bare = re.sub(r'^[^\w:]+', '', heading)
        if '/skills/' in name:
            hint = HINTS.get(list(SECTION_LABELS[language]).index(bare)) if bare in SECTION_LABELS[language] else None
        else:
            hint = HINTS['feature'] if bare.startswith(':') else HINTS['intro'] if not heading else HINTS['quick']
        result.append(f'{name}: "{heading or "introduction"}" is still to be written' + (f': {hint}' if hint else ''))
    return result


def plugin_entry_errors(name, prose, plugins):
    """The start page of a marketplace: one `### <plugin>` entry per listed plugin under Plugins, linking its README."""
    section = re.split(r'^## (?:[^\w\n]+ )?Plugins$', prose, flags=re.MULTILINE)
    if len(section) != 2:
        return []  # a missing section is already reported by the heading order
    parts = re.split(r'^### (.+)$', re.split(r'^## ', section[1], flags=re.MULTILINE)[0], flags=re.MULTILINE)
    entries = dict(zip((title.strip() for title in parts[1::2]), parts[2::2]))
    titles = {plugin.get('displayName') or plugin.get('name'): plugin.get('repository') or '' for plugin in plugins}
    errors = [f'{name}: Plugins lacks the entry ### {title}' for title in titles if title not in entries]
    errors += [f'{name}: Plugins names {title}, which marketplace.json does not list' for title in entries if title not in titles]
    for title, repository in titles.items():
        address = re.sub(r'\.git$', '', repository)
        if title in entries and address and f']({address}' not in entries[title]:
            errors.append(f'{name}: the entry {title} needs a link to the README of the plugin ({address})')
    return errors


def validate(output):
    root = Path(output).expanduser().resolve()
    errors = []
    try:
        policy = language_policy(root)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    kind = kind_of(root)
    pages = page_layout(policy, kind)
    skills = [skill_name(p) for p in sorted((root / 'skills').glob('*/SKILL.md'))] if kind == 'plugin' else []
    for language in policy['languages'] if kind == 'plugin' else ():  # one subpage per skill
        for skill in skills:
            pages[f'docs/{language}/skills/{skill}.md'] = (None, list(SECTION_LABELS[language]), language)
        for extra in sorted((root / 'docs' / language / 'skills').glob('*.md')):
            if skills and extra.stem not in skills:
                errors.append(f'docs/{language}/skills/{extra.name}: no skill of the plugin has this name')
    listed = bool(skills)  # documentation written outside the repository has no skills/ to compare with
    for language in policy['languages']:
        for former in FORMER_PAGES + (('plugins.md', 'files.md') if kind == 'marketplace' else ()):
            if (root / 'docs' / language / former).is_file():
                errors.append(f'docs/{language}/{former}: page of the former structure; remove it (nothing is converted)')
    for name, (_, required, language) in pages.items():
        path = safe_target(root, name)
        if not path.is_file():
            errors.append(f'{name}: missing page')
            continue
        text = path.read_text(encoding='utf-8')
        if re.search(r'\{\{[^}]+\}\}', text):
            by_hand = name.startswith('README') or '/skills/' in name
            errors += (open_sections(name, text, language) if by_hand else []) or [f'{name}: unresolved template placeholders']
        if text.count('```') % 2:
            errors.append(f'{name}: unclosed fenced block')
        prose = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        headings = re.findall(r'^## (.+)$', prose, re.MULTILINE)
        if name.startswith('README'):  # the start page may carry an icon before a heading
            headings = [re.sub(r'^[^\w]+', '', heading) for heading in headings]
        if name in EXACT_HEADINGS[kind]:
            if re.findall(r'^#{1,3} .+$', prose, re.MULTILINE) != EXACT_HEADINGS[kind][name]:
                errors.append(f'{name}: the headings must be exactly those of the generated page; run /plugin-manager:docs')
        elif name.endswith('/skills.md') and listed:  # generated: title, section and one entry per skill, one to one
            expected = ['# 🛠 Skills', '## 📖 Skills'] + ['### ' + skill for skill in skills]
            if re.findall(r'^#{1,3} .+$', prose, re.MULTILINE) != expected:
                errors.append(f'{name}: the headings must be exactly those of the generated page; run /plugin-manager:docs')
            for skill in skills:
                if f'](skills/{skill}.md)' not in prose:
                    errors.append(f'{name}: {skill} is not linked to its page skills/{skill}.md')
        elif headings != required:
            errors.append(f'{name}: level-two headings must match outline order')
        if name.startswith('README') and kind == 'plugin' and listed:
            errors += feature_errors(name, prose, skills, language)
        if name.startswith('README') and kind == 'marketplace':
            errors += plugin_entry_errors(name, prose, strict_json((root / 'marketplace.json').read_text(encoding='utf-8')).get('plugins', []))
        if len(re.findall(r'^# ', prose, re.MULTILINE)) != 1:
            errors.append(f'{name}: expected exactly one page title')
        if re.search(r'(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\Users\\)', text):
            errors.append(f'{name}: machine-specific path')
        if len(policy['languages']) > 1:
            other = 'en' if language == 'de' else 'de'
            if name.startswith('README'):
                counterpart = 'README.md' if other == policy['default_language'] else f'README.{other}.md'
            else:
                tail = name.split('/', 2)[2]  # below docs/<language>/
                counterpart = '../' * (tail.count('/') + 1) + other + '/' + tail
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
    icon = safe_target(root, 'assets/icon.png')  # the plugin's one icon (single source); the documentation only references it
    if not icon.is_file():
        errors.append('assets/icon.png is missing (the single icon of the plugin)')
    for name in (name for name in pages if name.startswith('README')):
        path = safe_target(root, name)
        if path.is_file() and 'assets/icon.png' not in path.read_text(encoding='utf-8'):
            errors.append(f'{name}: the icon assets/icon.png must be referenced')
    return errors


def check(source):
    """R37: findings are warnings, never a failure: whether the documentation is written is the developer's decision.
    Without docs/documentation.json no language is selected yet: nothing is checked, and the result says so."""
    root = Path(source).expanduser().resolve()
    manifest = root / 'docs/documentation.json'
    if not manifest.exists() and not manifest.is_symlink():
        return {'valid': True, 'check': 'docs', 'documentation': 'not_created', 'warnings': []}
    try:
        warnings = validate(root)
    except (OSError, ValueError) as exc:
        warnings = [str(exc)]
    result = {'valid': True, 'check': 'docs', 'documentation': 'checked', 'warnings': warnings}
    if warnings:
        result['next'] = 'Run /plugin-manager:docs to create the missing pages; write the texts yourself.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root')
    args = parser.parse_args(argv)
    result = check(args.source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if os.environ.get('GITHUB_ACTIONS') == 'true':  # shown on the run in GitHub without failing it
        for warning in result['warnings']:
            print('::warning::' + warning.replace('%', '%25').replace('\n', ' '))
    return 0


if __name__ == '__main__':
    sys.exit(main())
