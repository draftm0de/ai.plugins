#!/usr/bin/env python3
"""Package a plugin checkout in memory for the local development marketplace. Writes and installs nothing."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_KEY = 'io.zyris.distribution'


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


def read_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Expected a regular source file: {path}')
    return path.read_bytes()


def source_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Source paths must be repository-relative')
    path = root
    for part in Path(relative).parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f'Symlink in source: {relative}')
    return path


def configuration(root=None):
    root = Path(root) if root is not None else ROOT
    manifest = strict_json(read_file(root / 'plugin.json'))
    if not isinstance(manifest, dict):
        raise ValueError('plugin.json must be an object')
    name = manifest.get('name')
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Plugin name must be lowercase kebab-case')
    if 'version' in manifest:
        raise ValueError('Repository distribution follows commits; remove version from plugin.json')
    if not isinstance(manifest.get('description'), str) or not manifest['description'].strip():
        raise ValueError('Plugin description is required')
    if not isinstance(manifest.get('extensions', {}), dict):
        raise ValueError('extensions must be an object')
    config = manifest.get('extensions', {}).get(CONFIG_KEY, {})
    if not isinstance(config, dict) or set(config) - {'skillRoot', 'files', 'catalogs'}:
        raise ValueError('Unsupported distribution configuration')
    if not isinstance(config.get('catalogs', True), bool):
        raise ValueError('catalogs must be a boolean')
    skill_root = config.get('skillRoot', 'skills')
    if skill_root != 'skills':
        raise ValueError('Current plugin layout requires skillRoot=skills')
    if config.get('catalogs', False):
        raise ValueError('Plugin repositories must not own marketplace catalogs')
    for obsolete in ('.claude/skills', '.agents/skills', 'marketplace.json', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', '.codex-plugin/marketplace.json'):
        if (root/obsolete).exists() or (root/obsolete).is_symlink():
            raise ValueError('Unsupported host-local skill layout: ' + obsolete)
    source = source_path(root, skill_root)
    if not source.is_dir() or not list(source.glob('*/SKILL.md')):
        raise ValueError('skillRoot must contain canonical skill folders')
    market = name
    if 'marketplace' in config:
        raise ValueError('Unsupported distribution configuration: marketplace')
    if not isinstance(market, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', market):
        raise ValueError('Invalid marketplace name')
    extra = config.get('files', {})
    if not isinstance(extra, dict):
        raise ValueError('Distribution files must map destination paths to source paths')
    for destination, origin in extra.items():
        if (not isinstance(destination, str) or not destination or Path(destination).is_absolute()
                or any(part in ('.', '..') or part.startswith('.') for part in destination.split('/'))
                or destination == 'plugin.json'):
            raise ValueError('Unsafe or reserved distribution destination')
        if isinstance(origin, str) and (any(part.startswith('.env') for part in Path(origin).parts) or Path(origin).suffix in ('.pem', '.key')):
            raise ValueError('Private distribution source forbidden')
        for mapped in (destination, origin):
            if isinstance(mapped, str) and (set(Path(mapped).parts) & {'.git', '.local', '.tmp', 'dist', '.idea', '.venv', 'node_modules', '__pycache__', '.DS_Store'} or Path(mapped).suffix in ('.pyc', '.pyo', '.pyd')):
                raise ValueError('Generated/local files cannot be distributed: ' + mapped)
        if not source_path(root, origin).is_file():
            raise ValueError('Distribution source file missing: ' + str(origin))
    return manifest, source, market, extra


# Dot-named files that skeleton templates legitimately need. Exact names, files only,
# and only below a `templates` folder of a skill, plus the workflow folder of a template;
# every other dot path stays excluded.
TEMPLATE_DOT_FILES = frozenset({'.gitignore.tpl', '.gitkeep'})


def allowed_resource(destination, relative, part):
    parts = relative.parts
    if destination != 'skills' or 'templates' not in parts[:-1]:
        return False
    dotted = [index for index, name in enumerate(parts) if name.startswith('.')]
    if len(dotted) != 1:
        return False
    index = dotted[0]
    if part == '.github':  # the CI workflow a template delivers: only <kind>/sync/.github/workflows/<file>
        return parts.index('templates') < index and parts[index - 1] == 'sync' and parts[index + 1:-1] == ('workflows',)
    return part in TEMPLATE_DOT_FILES and part == parts[-1]


def payload():
    manifest, skill_root, market, extra = configuration()
    # Host metadata is derived from the portable manifest; no duplicate version source.
    claude = {key: manifest[key] for key in ('name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords') if key in manifest}
    display_name = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName')
    if display_name:
        claude['displayName'] = display_name
    files = {}
    def collect(folder, destination):
        if not folder.exists():
            return
        if folder.is_symlink():
            raise ValueError('Symlink in distributable source')
        for path in sorted(folder.rglob('*')):
            relative = path.relative_to(folder)
            if path.is_symlink():
                raise ValueError(f'Symlink in distributable source: {relative}')
            if any(part.startswith('.env') for part in relative.parts) or path.suffix in ('.key', '.pem'):
                raise ValueError(f'Private file in distributable source: {relative}')
            if any((part.startswith('.') and not allowed_resource(destination, relative, part)) or part in ('__pycache__','node_modules','dist') for part in relative.parts) or path.suffix in ('.pyc', '.pyo', '.pyd'):
                continue
            if path.is_file():
                files[str(Path(destination) / relative)] = read_file(path)
    collect(skill_root, 'skills')
    collect(ROOT / 'assets', 'assets')
    for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt'):
        if (ROOT / name).exists():
            files[name] = read_file(ROOT / name)
    for destination, origin in extra.items():
        data = read_file(source_path(ROOT, origin))
        if destination in files and files[destination] != data:
            raise ValueError('Conflicting distribution destination: ' + destination)
        files[destination] = data
    # Default package description is derived, not another manually maintained README.
    files.setdefault('README.md', ('# ' + manifest['name'] + '\n\n' + manifest['description'] +
        '\n\nThis plugin bundles its canonical skills. Activate it in your host and ask for its capabilities. '
        'Its source instructions define usage and limitations. Local packaging does not publish or install the plugin. '
        'Review host permissions and test behavior before deploying to production.\n').encode())
    commands = {}
    if (ROOT / 'commands').is_symlink():
        raise ValueError('Commands directory must not be a symlink')
    for path in sorted((ROOT / 'commands').glob('*.md')):
        commands['commands/' + path.name] = read_file(path)
    onboarding = manifest.get('extensions', {}).get('com.openai', {}).get('onboardingSkill')
    if onboarding and onboarding.removeprefix('./') not in files:
        raise ValueError('onboardingSkill does not exist in packaged payload')
    interface = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {})
    for field in ('logo', 'composerIcon'):
        value = interface.get(field)
        if value and value.removeprefix('./') not in files:
            raise ValueError('Host asset missing from payload: ' + field)
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode())
    for name, content in sorted({**files, **commands}.items()):
        fingerprint.update(name.encode() + b'\0' + content + b'\0')
    # Local snapshots use a content-derived cache identifier.
    # Direct repository imports use the unversioned manifests checked into Git.
    version = '0.0.0-dev.h' + fingerprint.hexdigest()[:12]
    manifest['version'] = claude['version'] = version
    # Local build configuration is not a runtime host extension.
    if 'extensions' in manifest:
        manifest['extensions'].pop(CONFIG_KEY, None)
    encode = lambda data: (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    return version, dict(files, **{'plugin.json': encode(manifest)}), dict(files, **commands, **{'.claude-plugin/plugin.json': encode(claude)})


def codex_payload(portable):
    manifest = strict_json(portable['plugin.json'])
    codex = {key: manifest[key] for key in ('name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords') if key in manifest}
    codex['skills'] = './skills/'
    interface = manifest.get('extensions', {}).get('com.openai', {}).get('interface')
    if interface:
        codex['interface'] = interface
    files = {name: content for name, content in portable.items() if name != 'plugin.json'}
    files['.codex-plugin/plugin.json'] = (json.dumps(codex, ensure_ascii=False, indent=2) + '\n').encode()
    return files
