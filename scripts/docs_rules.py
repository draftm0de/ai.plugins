#!/usr/bin/env python3
"""The structure rules of the documentation (R34, R37): read-only, used by verify in every repository and by the
documentation skill. Managed by the plugin manager: do not edit."""
import json
from pathlib import Path
import re
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
OUTLINE = {'plugin': {'README.md': ['Was es tut', 'Für wen', 'Welches Problem es löst', 'Daten und Datenschutz', 'Dokumentation'],
            'README.en.md': ['What it does', 'Who it is for', 'What it solves', 'Data and privacy', 'Documentation'],
            'docs/de/installation.md': ['Claude', 'Codex', 'Aktualisieren', 'Entfernen'],
            'docs/de/skills.md': ['Überblick'],
            'docs/de/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
            'docs/de/development.md': ['Voraussetzungen', 'Einrichten', 'Lokal testen', 'Befehle', 'CI', 'Gemeinsame Dateien', 'Veröffentlichen'],
            'docs/en/installation.md': ['Claude', 'Codex', 'Update', 'Remove'],
            'docs/en/skills.md': ['Overview'],
            'docs/en/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
            'docs/en/development.md': ['Requirements', 'Set up', 'Test locally', 'Commands', 'CI', 'Shared files', 'Publish']},
 'marketplace': {'README.md': ['Was es bietet', 'Für wen', 'Dokumentation'],
                 'README.en.md': ['What it offers', 'Who it is for', 'Documentation'],
                 'docs/de/installation.md': ['Claude', 'Codex', 'Aktualisieren', 'Entfernen'],
                 'docs/de/plugins.md': ['Überblick'],
                 'docs/de/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
                 'docs/de/development.md': ['Voraussetzungen', 'Einrichten', 'Lokal testen', 'Befehle', 'CI', 'Gemeinsame Dateien', 'Veröffentlichen'],
                 'docs/en/installation.md': ['Claude', 'Codex', 'Update', 'Remove'],
                 'docs/en/plugins.md': ['Overview'],
                 'docs/en/concepts.md': ['Marketplace', 'Plugin', 'Skill'],
                 'docs/en/development.md': ['Requirements', 'Set up', 'Test locally', 'Commands', 'CI', 'Shared files', 'Publish']}}
SECTION_LABELS = {'de': ('Beschreibung', 'Ablauf', 'Beispiel', 'Liest und schreibt'),
                  'en': ('Description', 'Workflow', 'Example', 'Reads and writes')}
MANAGED_PAGES = ('/concepts.md', '/development.md')
# pages of the former structure: reported, never converted or deleted
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
    listed = bool(skills)  # documentation written outside the repository has no skills/ to compare with
    for language in policy['languages']:
        for former in FORMER_PAGES:
            if (root / 'docs' / language / former).is_file():
                errors.append(f'docs/{language}/{former}: page of the former structure; remove it (nothing is converted)')
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
        found_skills = skills if listed else headings[len(required):]
        expected = required + found_skills if name.endswith('/skills.md') else required
        if headings != expected:
            errors.append(f'{name}: level-two headings must match outline order' + (' (Overview, then one section per skill)' if name.endswith('/skills.md') else ''))
        if name.endswith('/skills.md'):
            sections = re.split(r'^## .+$', prose, flags=re.MULTILINE)[2:]
            for skill, section in zip(found_skills, sections):
                if re.findall(r'^### (.+)$', section, re.MULTILINE) != list(SECTION_LABELS[language]):
                    errors.append(f'{name}: {skill} needs the sections ' + ', '.join(SECTION_LABELS[language]))
                if listed and '| [' + skill + '](' not in prose:
                    errors.append(f'{name}: {skill} has no row in the overview table')
        if len(re.findall(r'^# ', prose, re.MULTILINE)) != 1:
            errors.append(f'{name}: expected exactly one page title')
        if re.search(r'(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\Users\\)', text):
            errors.append(f'{name}: machine-specific path')
        if len(policy['languages']) > 1 and not name.endswith(MANAGED_PAGES):  # managed pages carry no language switch
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
    icon = safe_target(root, 'assets/icon.png')  # the plugin's one icon (single source); the documentation only references it
    if not icon.is_file():
        errors.append('assets/icon.png is missing (the single icon of the plugin)')
    for name in (name for name in pages if name.startswith('README')):
        path = safe_target(root, name)
        if path.is_file() and 'assets/icon.png' not in path.read_text(encoding='utf-8'):
            errors.append(f'{name}: the icon assets/icon.png must be referenced')
    return errors
