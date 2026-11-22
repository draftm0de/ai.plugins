#!/usr/bin/env python3
"""Install working-tree snapshots through one shared development marketplace."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = '.draftmode-local-marketplace'

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


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded

def prepare(root, target):
    root = Path(root).resolve()
    catalogs = module(root/'scripts/marketplace.py', 'shared_catalog').expected(root)
    config = strict_json((root/'marketplace.json').read_text())
    local_file = root/'.local/marketplace.json'
    local = strict_json(local_file.read_text()) if local_file.exists() else {}
    sources = local.get('sources', {})
    if not isinstance(sources, dict):
        raise ValueError('Local sources must map plugin names to checkout paths')
    engine = module(Path(__file__).with_name('plugin_payload.py'), 'snapshot_payload')
    snapshots = {}
    for entry, catalog_entry in zip(config['plugins'], catalogs['.claude-plugin/marketplace.json']['plugins']):
        name = catalog_entry['name']
        if 'path' in entry:
            source = root/entry['path']
        else:
            configured = sources.get(name)
            if not isinstance(configured, str) or not configured:
                raise ValueError(f'Missing local checkout for {name}; configure sources.{name} in {local_file}')
            source = Path(configured).expanduser()
            if not source.is_absolute():
                source = root/source
        source = source.resolve()
        engine.ROOT = source
        manifest = engine.configuration()[0]
        if manifest['name'] != name:
            raise ValueError(f'Local identity mismatch for {name}: {source}')
        if 'repository' in entry and manifest.get('repository', '').removesuffix('.git') != entry['repository'].removesuffix('.git'):
            raise ValueError(f'Local repository metadata does not match catalog for {name}')
        version, portable, claude = engine.payload()
        files = claude if target == 'claude' else engine.codex_payload(portable)
        snapshots[name] = {'files': files, 'version': version, 'source': str(source)}
    marketplace = config['name'] + '-dev'
    catalog_key = '.claude-plugin/marketplace.json' if target == 'claude' else '.agents/plugins/marketplace.json'
    catalog = catalogs[catalog_key]
    catalog['name'] = marketplace
    if target == 'codex':
        catalog['interface']['displayName'] = config['displayName'] + ' (Development)'
    for entry in catalog['plugins']:
        name = entry['name']
        entry['source'] = './plugins/' + name if target == 'claude' else {'source': 'local', 'path': './plugins/' + name}
        if target == 'claude':
            entry['version'] = snapshots[name]['version']
    return marketplace, catalog_key, catalog, snapshots

def install_local(target, dry_run=False, root=ROOT):
    if target not in ('claude', 'codex'):
        raise ValueError('Local development supports claude or codex')
    root = Path(root).resolve()
    marketplace, catalog_key, catalog, snapshots = prepare(root, target)
    output = root/'dist/local-development'
    destination = output/(target + '-marketplace')
    # Reject foreign outputs before any replacement. Host caches are managed by the CLI.
    if any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ValueError('Development output must not use symlinks')
    marker = destination/MARKER
    if destination.exists() and (not marker.is_file() or marker.is_symlink() or marker.read_text().strip() != marketplace):
        raise ValueError('Refusing to replace an unowned development marketplace')
    output.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix='.staged-', dir=output))
    backup = None
    try:
        (staged/MARKER).write_text(marketplace + '\n')
        for name, snapshot in snapshots.items():
            for relative, content in snapshot['files'].items():
                path = staged/'plugins'/name/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        path = staged/catalog_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
        if destination.exists():
            backup = Path(tempfile.mkdtemp(prefix='.backup-', dir=output))
            backup.rmdir()
            destination.rename(backup)
        try:
            staged.rename(destination)
        except OSError:
            if backup:
                backup.rename(destination)
                backup = None
            raise
    finally:
        if staged.exists():
            shutil.rmtree(staged)
        if backup and backup.exists():
            shutil.rmtree(backup)
    commands = [[target, 'plugin', 'marketplace', 'add', str(destination)]]
    for name in snapshots:
        selector = name + '@' + marketplace
        commands.append(['codex', 'plugin', 'add', selector, '--json'] if target == 'codex' else
                        ['claude', 'plugin', 'install', selector, '--scope', 'user'])
    if not dry_run:
        if not shutil.which(target):
            raise ValueError(f'{target} CLI not found; snapshots prepared but no plugins installed')
        for command in commands:
            subprocess.run(command, check=True)
    return {'marketplace': marketplace, 'path': str(destination),
            'plugins': {name: {key: value for key, value in data.items() if key != 'files'} for name, data in snapshots.items()},
            'commands': commands, 'executed': not dry_run, 'published': False,
            'next': 'Open a new local session. Enable only the intended remote or development copy.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Snapshots use current checkouts, including uncommitted edits, on any branch. After edits/branch switches run install-local and open a new host session. No commit/push/PR or per-branch marketplace. Host CLI is only needed without --dry-run. Use configure; only .local/marketplace.json is runtime configuration.')
    parser.add_argument('action', choices=['install-local'])
    parser.add_argument('--target', choices=['claude', 'codex'], default='claude')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        result = install_local(args.target, args.dry_run)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
