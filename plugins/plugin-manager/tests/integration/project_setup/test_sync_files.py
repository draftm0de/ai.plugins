"""R16: the helper trusts the generated hash file only as the expected value (fictional parent, real helper)."""
import json
import unittest

from tests.support.project_setup_fixture import ALPHA, FictionalSandbox, tree


class SyncFileTests(unittest.TestCase):
    def setUp(self):
        self.box = FictionalSandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        self.sync_file = self.box.manager / 'skills/_shared/manifests/plugin.sync.json'

    def blocked(self, *fragments):
        before = tree(self.p)
        for operation in ('status', 'setup'):
            code, data, _ = self.box.call(operation)
            self.assertEqual((1, False, 'stop'), (code, data['ok'], data['next']), operation)
            conflict = data['conflicts'][0]
            self.assertEqual('template_base', conflict.get('code'), conflict)
            for fragment in fragments:
                self.assertIn(fragment, conflict['reason'] + conflict['path'])
        self.assertEqual(before, tree(self.p))  # nothing was written

    def test_changed_source_bytes_are_a_conflict_that_points_at_the_build_command(self):
        (self.box.sync_dir / 'alpha.md').write_bytes(ALPHA + b'edited without rebuilding the hashes\n')
        self.blocked('alpha.md', 'differs from its recorded hash', 'make build-skeleton-hashes')

    def test_listed_file_without_source_is_a_conflict_never_a_removal(self):
        (self.box.sync_dir / 'alpha.md').unlink()
        self.blocked('alpha.md', 'missing')

    def test_unlisted_file_in_sync_folder_is_a_conflict(self):
        (self.box.sync_dir / 'extra.md').write_text('not listed')
        self.blocked('extra.md', 'Unlisted')

    def test_a_tombstone_path_that_still_has_a_source_counts_as_unlisted(self):
        data = json.loads(self.sync_file.read_text())
        data['removed'] = ['alpha.md']; del data['files']['alpha.md']
        self.sync_file.write_text(json.dumps(data))
        self.blocked('alpha.md', 'Unlisted')

    def test_overlap_and_invalid_sync_files_are_conflicts(self):
        good = self.sync_file.read_text()
        data = json.loads(good); data['removed'] = ['alpha.md']
        self.sync_file.write_text(json.dumps(data))
        self.blocked('listed as synced file and as removed')
        for broken in ('{broken', json.dumps({'schema_version': 2, 'files': {}, 'removed': []}),
                       json.dumps({'schema_version': 1, 'files': {'alpha.md': {'sha256': 'x', 'executable': False}}, 'removed': []}),
                       json.dumps({'schema_version': 1, 'files': {}, 'removed': [], 'extra': 1})):
            self.sync_file.write_text(broken)
            self.blocked('plugin.sync.json')

    def test_tombstone_triggers_the_removal_rules_not_a_conflict(self):
        self.assertEqual(0, self.box.call('setup')[0])
        self.box.drop_template('alpha.md')
        code, data, _ = self.box.call('status')
        self.assertEqual((0, ['alpha.md'], 'skeleton'), (code, data['removals']['auto'], data['next']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertFalse((self.p / 'alpha.md').exists())

    def test_executable_bit_comes_from_the_hash_file(self):
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertTrue((self.p / 'tools/deep/gamma.sh').stat().st_mode & 0o111)
        self.assertFalse((self.p / 'alpha.md').stat().st_mode & 0o111)


if __name__ == '__main__':
    unittest.main()
