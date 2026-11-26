#!/usr/bin/env python3
"""Standards check: the managed standards and AGENTS.md are present, unchanged and not copied (R27, R28, R41). Read-only.
Usage: python3 -B scripts/verify/standards.py --source <repository>. Managed by the plugin manager: do not edit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from common import kind_of, outcome, strict_json


# The managed standard files of each kind, what the managed AGENTS.md must name, and the files that never copy them.
STANDARDS = {'plugin': (tuple('docs/standards/' + n + '.md' for n in ('coding', 'messages', 'testing', 'skills')),
                        'docs/standards', ('SCOPE.md', 'CUSTOM.AGENTS.md')),
             'marketplace': (('SCOPE.md',), 'SCOPE.md', ('CUSTOM.AGENTS.md',))}  # R41: its scope is its standard


def recorded_hashes(root):
    """{path: {sha256}} of the managed files as the plugin's committed skeleton lock records their source; empty when
    there is no readable lock (setup reports a damaged one)."""
    found = {}
    for lock in sorted((root / '.project/plugins').glob('*/skeleton.json')):
        if lock.is_symlink():
            continue
        try:
            files = strict_json(lock.read_text(encoding='utf-8'))['files']
            found.update({path: {'sha256': entry['source_hash']} for path, entry in files.items() if entry.get('source_hash')})
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            continue
    return found


def standards(root, kind='plugin'):
    """R27/R28/R41: the managed standards of the kind and the managed AGENTS.md are in the repository, unchanged, and not
    copied into SCOPE.md or CUSTOM.AGENTS.md. Next to the Manager's own runtime the hashes of the managed files are known;
    a copy of this script inside a repository checks presence, the reference and the copy rule only."""
    files, named, writable = STANDARDS[kind]
    problems = []
    manifest = Path(__file__).resolve().parents[2] / 'manifests' / (kind + '.sync.json')
    if manifest.is_file():
        known = strict_json(manifest.read_text(encoding='utf-8')).get('files', {})
    else:  # a copy of this script inside a repository (for example in CI): compare with what setup recorded in the committed lock
        known = recorded_hashes(root)
    texts = []
    for name in files:
        path = root / name
        if path.is_symlink() or not path.is_file():
            problems.append(name + ' is missing')
            continue
        data = path.read_bytes()
        texts.append(data.decode('utf-8', 'replace'))
        expected = known.get(name, {}).get('sha256')
        if expected and hashlib.sha256(data).hexdigest() != expected:
            problems.append(name + ' differs from the managed standard')
    agents = root / 'AGENTS.md'
    agents_data = agents.read_bytes() if agents.is_file() and not agents.is_symlink() else None
    if agents_data is None:
        problems.append('AGENTS.md is missing')
    else:
        expected = known.get('AGENTS.md', {}).get('sha256')
        if expected and hashlib.sha256(agents_data).hexdigest() != expected:
            problems.append('AGENTS.md differs from the managed one (own instructions belong into CUSTOM.AGENTS.md)')
        if named.encode() not in agents_data:
            problems.append('AGENTS.md does not tell to read ' + named)
    own = [root / name for name in writable]
    own_texts = {path.name: path.read_text(encoding='utf-8', errors='replace') for path in own if path.is_file() and not path.is_symlink()}
    copied = [(name, line.strip()) for text in texts for line in text.splitlines() if len(line.strip()) >= 60
              for name, own_text in own_texts.items() if line.strip() in own_text]
    if copied:
        problems.append(copied[0][0] + ' copies standard text: ' + copied[0][1][:60] + '...')
    if problems:
        raise ValueError('The managed standards are not in place: ' + '; '.join(problems)
                         + '. A standard is never edited in a repository; run /plugin-manager:setup (in Codex: $plugin-manager:setup) to bring the managed files back.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root')
    parser.add_argument('--kind', choices=['auto', 'plugin', 'marketplace'], default='auto')
    args = parser.parse_args(argv)
    result = outcome('standards', args.source, lambda root: standards(root, kind_of(root, args.kind)))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
