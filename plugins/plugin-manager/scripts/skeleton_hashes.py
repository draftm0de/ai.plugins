#!/usr/bin/env python3
"""Development tool: build or check the generated skeleton hash files (skills/_shared/manifests/<kind>.sync.json).

build  writes <kind>.sync.json from templates/<kind>/sync/ (sha256 and executable bit per file, sorted) and keeps the
       `removed` tombstones of an existing file.
check  verifies the files against the folders and exits 1 naming each path that deviates.
Not runtime code: it is neither shipped to nor run in generated repositories.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

SHA256 = re.compile(r'[0-9a-f]{64}')
KEYS = {'schema_version', 'files', 'removed'}


def safe(path):
    return (isinstance(path, str) and path != '' and not path.startswith('/') and '\\' not in path
            and all(part not in ('', '.', '..') for part in path.split('/')))


def kinds(root):
    manifests = Path(root) / 'skills/_shared/manifests'
    names = {p.name[:-len('.sync.json')] for p in manifests.glob('*.sync.json')}
    names |= {p.stem for p in manifests.glob('*.json') if '.' not in p.stem}
    return manifests, sorted(names)


def scan(sync_dir):
    """Actual files below sync/: {path: {sha256, executable}}; symlinks and special files are errors."""
    found, problems = {}, []
    if not sync_dir.is_dir():
        return found, problems
    for current, directories, names in os.walk(sync_dir):
        for entry in [*directories, *names]:
            full = Path(current) / entry
            relative = str(full.relative_to(sync_dir))
            if full.is_symlink():
                problems.append(f'{relative}: symlink in sync/')
            elif entry in names:
                mode = full.stat().st_mode
                found[relative] = {'sha256': hashlib.sha256(full.read_bytes()).hexdigest(), 'executable': bool(mode & 0o111)}
    return found, problems


def render(files, removed):
    return json.dumps({'schema_version': 1, 'files': dict(sorted(files.items())), 'removed': sorted(removed)}, indent=2) + '\n'


def read_sync(path):
    """(data, problems); a missing file returns (None, [])."""
    if not path.is_file():
        return None, []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        return None, [f'{path.name}: invalid JSON ({exc})']
    problems = []
    if not (isinstance(data, dict) and set(data) == KEYS and type(data['schema_version']) is int and data['schema_version'] == 1
            and isinstance(data['files'], dict) and isinstance(data['removed'], list)):
        return None, [f'{path.name}: unsupported format (schema_version 1 with files and removed)']
    for key, value in data['files'].items():
        if not (safe(key) and isinstance(value, dict) and set(value) == {'sha256', 'executable'}
                and isinstance(value['sha256'], str) and SHA256.fullmatch(value['sha256']) and type(value['executable']) is bool):
            problems.append(f'{path.name}: invalid entry {key!r}')
    if not all(safe(v) for v in data['removed']) or len(set(data['removed'])) != len(data['removed']):
        problems.append(f'{path.name}: invalid or duplicate removed entries')
    return (None if problems else data), problems


def build(root):
    manifests, names = kinds(root)
    problems = []
    for name in names:
        if not (manifests / f'{name}.json').is_file():
            problems.append(f'{name}: manifests/{name}.json is missing')
            continue
        sync_path = manifests / f'{name}.sync.json'
        old, errors = read_sync(sync_path)
        removed = old['removed'] if old else []
        if errors:
            problems += errors
            continue
        files, scan_problems = scan(Path(root) / 'skills/_shared/templates' / name / 'sync')
        problems += [f'{name}: {p}' for p in scan_problems]
        both = sorted(set(files) & set(removed))
        if both:
            problems.append(f'{name}: listed as file and as removed: {", ".join(both)}')
        if scan_problems or both:
            continue
        text = render(files, removed)
        if not sync_path.exists() or sync_path.read_text(encoding='utf-8') != text:
            descriptor, temporary = tempfile.mkstemp(prefix='.sync-', dir=manifests)
            with os.fdopen(descriptor, 'w', encoding='utf-8', newline='') as handle:
                handle.write(text)
            os.replace(temporary, sync_path)
            print(f'wrote {sync_path.relative_to(root)}')
    return problems


def check(root):
    manifests, names = kinds(root)
    problems = []
    if not names:
        problems.append('no kind found under skills/_shared/manifests')
    for name in names:
        if not (manifests / f'{name}.json').is_file():
            problems.append(f'{name}: manifests/{name}.json is missing')
        sync_path = manifests / f'{name}.sync.json'
        data, errors = read_sync(sync_path)
        if data is None and not errors:
            problems.append(f'{name}: manifests/{name}.sync.json is missing (run make build-skeleton-hashes)')
        problems += [f'{name}: {e}' for e in errors]
        if data is None:
            continue
        overlap = sorted(set(data['files']) & set(data['removed']))
        if overlap:
            problems.append(f'{name}: listed as file and as removed: {", ".join(overlap)}')
        actual, scan_problems = scan(Path(root) / 'skills/_shared/templates' / name / 'sync')
        problems += [f'{name}: {p}' for p in scan_problems]
        for path in sorted(set(data['files']) - set(actual)):
            problems.append(f'{name}: {path}: listed but missing in sync/')
        for path in sorted(set(actual) - set(data['files'])):
            problems.append(f'{name}: {path}: in sync/ but not listed')
        for path in sorted(set(actual) & set(data['files'])):
            if actual[path]['sha256'] != data['files'][path]['sha256']:
                problems.append(f'{name}: {path}: hash differs from sync file')
            elif actual[path]['executable'] != data['files'][path]['executable']:
                problems.append(f'{name}: {path}: executable bit differs from sync file')
        if not overlap and sync_path.read_text(encoding='utf-8') != render(data['files'], data['removed']):
            problems.append(f'{name}: manifests/{name}.sync.json is not in canonical form (sorted, 2-space JSON, trailing newline)')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=('build', 'check'))
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]), help='Plugin root (default: this repository)')
    args = parser.parse_args(argv)
    problems = (build if args.action == 'build' else check)(Path(args.root))
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f'skeleton hashes: {len(problems)} problem(s); run make build-skeleton-hashes' if args.action == 'check'
              else f'skeleton hashes: {len(problems)} problem(s)', file=sys.stderr)
        return 1
    if args.action == 'check':
        print('skeleton hashes: ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
