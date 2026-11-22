"""R16: scripts/skeleton_hashes.py builds and checks the generated hash files (fictional kinds only)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
TOOL = ROOT / 'scripts/skeleton_hashes.py'


class ToolBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'skills/_shared/manifests').mkdir(parents=True)
        self.write('skills/_shared/manifests/demo.json', json.dumps({'schema_version': 1, 'product': None, 'derived': []}))
        self.write('skills/_shared/templates/demo/sync/b.txt', 'bee\n')
        self.write('skills/_shared/templates/demo/sync/a/run.sh', '#!/bin/sh\n', mode=0o755)
        self.write('skills/_shared/templates/demo/seed/once.md', 'seed\n')

    def write(self, relative, text, mode=0o644):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(mode)

    def run_tool(self, action):
        return subprocess.run([sys.executable, '-B', str(TOOL), action, '--root', str(self.root)], capture_output=True, text=True)

    def sync_path(self):
        return self.root / 'skills/_shared/manifests/demo.sync.json'

    def build_ok(self):
        result = self.run_tool('build')
        self.assertEqual(0, result.returncode, result.stderr)


class BuildTests(ToolBase):
    def test_build_lists_only_sync_files_sorted_with_hash_and_executable_and_is_deterministic(self):
        self.build_ok()
        first = self.sync_path().read_bytes()
        data = json.loads(first)
        self.assertEqual(['a/run.sh', 'b.txt'], list(data['files']))
        self.assertEqual([True, False], [v['executable'] for v in data['files'].values()])
        self.assertEqual({'schema_version', 'files', 'removed'}, set(data))
        self.assertEqual([], data['removed'])
        self.assertTrue(first.endswith(b'\n'))
        self.assertNotIn('once.md', json.dumps(data))  # seeds are never hashed
        self.build_ok()
        self.assertEqual(first, self.sync_path().read_bytes())
        self.assertEqual('', self.run_tool('build').stdout)  # unchanged: nothing is rewritten or announced

    def test_build_keeps_tombstones_and_rejects_overlap(self):
        self.write('skills/_shared/manifests/demo.sync.json', json.dumps({'schema_version': 1, 'files': {}, 'removed': ['gone.md']}))
        self.build_ok()
        self.assertEqual(['gone.md'], json.loads(self.sync_path().read_text())['removed'])
        self.write('skills/_shared/manifests/demo.sync.json', json.dumps({'schema_version': 1, 'files': {}, 'removed': ['b.txt']}))
        before = self.sync_path().read_bytes()
        result = self.run_tool('build')
        self.assertEqual(1, result.returncode)
        self.assertIn('b.txt', result.stderr)
        self.assertEqual(before, self.sync_path().read_bytes())


class CheckTests(ToolBase):
    def setUp(self):
        super().setUp()
        self.build_ok()

    def assert_fails(self, *fragments):
        result = self.run_tool('check')
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_green_after_build(self):
        result = self.run_tool('check')
        self.assertEqual((0, 'skeleton hashes: ok\n'), (result.returncode, result.stdout))

    def test_changed_bytes_fail_naming_the_path(self):
        self.write('skills/_shared/templates/demo/sync/b.txt', 'changed\n')
        self.assert_fails('b.txt', 'hash differs')

    def test_executable_flip_fails(self):
        (self.root / 'skills/_shared/templates/demo/sync/a/run.sh').chmod(0o644)
        self.assert_fails('a/run.sh', 'executable')

    def test_unlisted_and_missing_files_fail(self):
        self.write('skills/_shared/templates/demo/sync/new.txt', 'x')
        (self.root / 'skills/_shared/templates/demo/sync/b.txt').unlink()
        self.assert_fails('new.txt: in sync/ but not listed', 'b.txt: listed but missing')

    def test_missing_sync_file_invalid_file_overlap_and_noncanonical_form_fail(self):
        original = self.sync_path().read_text()
        self.sync_path().unlink()
        self.assert_fails('demo.sync.json is missing', 'make build-skeleton-hashes')
        self.sync_path().write_text('{not json')
        self.assert_fails('invalid JSON')
        data = json.loads(original); data['removed'] = ['b.txt']
        self.sync_path().write_text(json.dumps(data, indent=2) + '\n')
        self.assert_fails('listed as file and as removed')
        self.sync_path().write_text(original.replace('\n', '', 1))
        self.assert_fails('canonical form')

    def test_seed_changes_and_symlinks(self):
        self.write('skills/_shared/templates/demo/seed/once.md', 'edited seed\n')
        self.assertEqual(0, self.run_tool('check').returncode)  # seeds are not hashed
        (self.root / 'skills/_shared/templates/demo/sync/link.txt').symlink_to(self.root)
        self.assert_fails('link.txt: symlink in sync/')


if __name__ == '__main__':
    unittest.main()
