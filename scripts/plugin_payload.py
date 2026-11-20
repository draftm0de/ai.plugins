#!/usr/bin/env python3
"""Validate repository imports and manage local development snapshots. Never publish implicitly."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = '.zyris-generated'
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


def repository_files(manifest=None):
    """Derive committed host metadata from the portable identity; no version pins."""
    manifest = manifest or configuration()[0]
    if 'version' in manifest:
        raise ValueError('Repository distribution follows commits; remove version from plugin.json')
    name = manifest['name']
    config = manifest.get('extensions', {}).get(CONFIG_KEY, {})
    market = name
    if 'marketplace' in config:
        raise ValueError('Unsupported distribution configuration: marketplace')
    interface = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {})
    claude = {key: manifest[key] for key in ('name', 'description', 'author', 'homepage', 'repository', 'license', 'keywords') if key in manifest}
    display_name = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName')
    if display_name:
        claude['displayName'] = display_name
    if config.get('catalogs', False):
        raise ValueError('Plugin repositories must not own marketplace catalogs')
    return {'.claude-plugin/plugin.json': claude}


def repository_metadata(check=False):
    expected = repository_files()
    for relative in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
        if (ROOT / relative).exists():
            raise ValueError('Plugin repository must not own marketplace catalogs: ' + relative)
    targets = {relative: source_path(ROOT, relative) for relative in expected}
    drift = []
    for relative, data in expected.items():
        path = targets[relative]
        if not path.is_file() or strict_json(read_file(path)) != data:
            drift.append(relative)
    if check and drift:
        raise ValueError('Repository metadata missing or stale: ' + ', '.join(drift) + '; run make sync-plugin')
    if not check:
        for relative in drift:
            path = targets[relative]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(expected[relative], ensure_ascii=False, indent=2) + '\n')
    return {'valid': True, 'files': list(expected), 'updated': [] if check else drift}


# Dot-named files that skeleton templates legitimately need. Exact names, files only,
# and only below a `templates` folder of a skill; every other dot path stays excluded.
TEMPLATE_DOT_FILES = frozenset({'.gitignore.tpl', '.gitkeep'})


def allowed_resource(destination, relative, part):
    parts = relative.parts
    return (destination == 'skills' and part in TEMPLATE_DOT_FILES and part == parts[-1]
            and 'templates' in parts[:-1] and not any(p.startswith('.') for p in parts[:-1]))


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


def install_local(target, update=False, dry_run=False, marketplace_root=None):
    """Resolve the selected development marketplace; never fall back to a private catalog."""
    if target not in ('claude', 'codex'):
        raise ValueError('Local development supports claude or codex')
    selected = marketplace_root
    if not selected:
        path = source_path(ROOT, '.local/marketplace.json')
        if path.exists():
            selected = strict_json(read_file(path)).get('marketplace')
    if selected:
        selected = Path(selected).expanduser()
        if not selected.is_absolute():
            selected = ROOT / selected
    if not selected:
        raise ValueError('Local marketplace unavailable; run configure or pass --marketplace PATH')
    selected = Path(selected).resolve()
    helper = selected / 'scripts/local_plugins.py'
    if not helper.is_file() or helper.is_symlink():
        raise ValueError('Selected marketplace is unavailable or lacks local development tooling')
    catalog = strict_json(read_file(selected / 'marketplace.json'))
    name = configuration()[0]['name']
    local_file = selected / '.local/marketplace.json'
    sources = strict_json(read_file(local_file)).get('sources', {}) if local_file.exists() else {}
    linked = False
    for entry in catalog['plugins']:
        path = entry.get('path') if 'path' in entry else sources.get(entry.get('name'))
        if path:
            candidate = Path(path).expanduser()
            candidate = candidate if candidate.is_absolute() else selected / candidate
            if candidate.resolve() == ROOT.resolve() and (entry.get('name', name) == name):
                linked = True
    if not linked:
        raise ValueError('Plugin is not locally associated with the selected marketplace; run configure')
    spec = importlib.util.spec_from_file_location('selected_local_marketplace', helper)
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    return shared.install_local(target, update, dry_run, root=selected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog='Git + Python 3.10+ management tools; Make optional. Local snapshots use the current checkout on any branch. After edits/branch switches run update-local and start a new host session. No commit/push/PR; host CLI only for automatic installation.')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('install-local', 'update-local'):
        action = sub.add_parser(command)
        action.add_argument('--target', choices=('claude', 'codex'), default='claude')
        action.add_argument('--dry-run', action='store_true')
        action.add_argument('--marketplace', type=Path)
    check = sub.add_parser('check')
    sub.add_parser('sync')
    args = parser.parse_args(argv)
    try:
        if args.command in ('check', 'sync'):
            result = repository_metadata(check=args.command == 'check')
        else:
            result = install_local(args.target, args.command == 'update-local', args.dry_run, args.marketplace)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
