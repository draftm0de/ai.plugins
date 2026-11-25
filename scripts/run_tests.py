#!/usr/bin/env python3
"""Run an explicit test layer using only the Python standard library."""
import argparse
import os
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
KINDS = ('unit', 'integration', 'contracts', 'native')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('deterministic',) + KINDS, default='deterministic')
    parser.add_argument('--group', help='Optional skill/component, e.g. plugin-create or setup')
    parser.add_argument('--list', action='store_true', help='Collect tests without executing them')
    args = parser.parse_args()
    group = args.group.replace('-', '_') if args.group else None
    if group and (not group.isidentifier() or group.startswith('_')):
        parser.error('Group must be a skill/component identifier')
    os.environ['AI_PLUGIN_TEST_NATIVE'] = '1' if args.kind == 'native' else '0'
    layers = ('unit', 'integration', 'contracts') if args.kind == 'deterministic' else (args.kind,)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for layer in layers:
        path = ROOT/'tests'/layer
        if group:
            path /= group
        if path.is_dir():
            suite.addTests(loader.discover(str(path), pattern='test_*.py', top_level_dir=str(ROOT)))
    if loader.errors:
        for error in loader.errors:
            print(error, file=sys.stderr)
        return 1
    count = suite.countTestCases()
    if not count:
        print('NOT RUN: no tests configured for ' + args.kind + ('/' + group if group else ''))
        return 1 if group else 0
    if args.list:
        def identifiers(items):
            for item in items:
                if isinstance(item, unittest.TestSuite):
                    yield from identifiers(item)
                else:
                    yield item.id()
        for identifier in identifiers(suite):
            print(identifier)
        print(str(count) + ' tests collected')
        return 0
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
