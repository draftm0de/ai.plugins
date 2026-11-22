"""Acceptance tests R15-R17: workpackage configuration evidence per running plugin (fictional projects only)."""
import json
import unittest

from tests.support.project_setup_fixture import Sandbox, tree

PLUGIN = 'plugin-manager'
EVIDENCE = '.project/plugins/' + PLUGIN + '/config.json'
SKELETON = '.project/plugins/' + PLUGIN + '/skeleton.json'
OLD_LOCK = '.project/plugin.skeleton.lock.json'


class WorkpackageBase(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(configured=False); self.addCleanup(self.box.close)
        self.p = self.box.project

    def status(self, plugin=PLUGIN):
        code, data, result = self.box.call('status', '--plugin', plugin)
        return code, data, result

    def language(self):
        code, data, result = self.box.call('language', '--language', 'de')
        self.assertEqual(0, code, result.stderr + result.stdout)

    def evidence(self, path=EVIDENCE, **override):
        data = {'schema_version': 1, 'plugin': PLUGIN, 'kind': 'plugin', 'artifact': 'demo-plugin',
                'configured_at': '2026-11-22T10:00:00Z'}
        data.update(override)
        target = self.p / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))


class ConfigurationEvidenceTests(WorkpackageBase):
    def test_language_missing_has_priority_over_configuration(self):
        _, data, _ = self.status()
        self.assertEqual('language', data['next'])

    def test_root_plugin_json_is_not_evidence(self):
        self.language()
        _, data, _ = self.status()
        self.assertTrue((self.p / 'plugin.json').exists())
        self.assertEqual('configure', data['next'])
        self.assertEqual({'plugin': PLUGIN, 'configured': False, 'kind': None}, data['configuration'])

    def test_valid_evidence_configures_the_workpackage_for_that_kind(self):
        self.language(); self.evidence()
        _, data, _ = self.status()
        self.assertNotEqual('configure', data['next'])
        self.assertEqual({'plugin': PLUGIN, 'configured': True, 'kind': 'plugin'}, data['configuration'])

    def test_evidence_of_another_plugin_does_not_configure_this_one(self):
        self.language()
        self.evidence('.project/plugins/other-plugin/config.json', plugin='other-plugin')
        _, data, _ = self.status()
        self.assertEqual('configure', data['next'])
        _, other, _ = self.status('other-plugin')
        self.assertTrue(other['configuration']['configured'])

    def test_marketplace_kind_allows_root_marketplace_json(self):
        self.language(); self.evidence(kind='marketplace', artifact='demo-marketplace')
        (self.p / 'plugin.json').unlink()
        (self.p / 'marketplace.json').write_text(json.dumps({'name': 'demo-marketplace'}))
        code, data, _ = self.status()
        self.assertEqual((0, True, 'marketplace'), (code, data['ok'], data['configuration']['kind']))

    def test_invalid_evidence_stops_without_writes(self):
        self.language()
        for override in ({'kind': 'website'}, {'extra': 1}, {'schema_version': 2}, {'plugin': 'other-plugin'},
                         {'artifact': 5}, {'configured_at': 'yesterday'}):
            with self.subTest(override=override):
                self.evidence(**override)
                before = tree(self.p)
                code, data, _ = self.status()
                self.assertEqual((1, False, 'stop'), (code, data['ok'], data['next']))
                self.assertIn(EVIDENCE, [c['path'] for c in data['conflicts']])
                self.assertEqual(before, tree(self.p))

    def test_corrupt_evidence_is_a_conflict_not_missing(self):
        self.language()
        (self.p / EVIDENCE).parent.mkdir(parents=True)
        (self.p / EVIDENCE).write_text('{not json')
        code, data, _ = self.status()
        self.assertEqual((1, 'stop'), (code, data['next']))


class SkeletonEvidenceTests(WorkpackageBase):
    def test_old_lock_location_is_rejected_before_writes(self):
        self.language(); self.evidence()
        (self.p / OLD_LOCK).write_text(json.dumps({'schema_version': 2, 'files': {}}))
        before = tree(self.p)
        code, data, _ = self.status()
        self.assertEqual((1, 'stop'), (code, data['next']))
        self.assertIn(OLD_LOCK, [c['path'] for c in data['conflicts']])
        code, data, _ = self.box.call('setup', '--plugin', PLUGIN)
        self.assertEqual(1, code)
        self.assertEqual(before, tree(self.p))

    def test_setup_records_skeleton_evidence_per_plugin(self):
        self.language(); self.evidence()
        code, data, result = self.box.call('setup', '--plugin', PLUGIN)
        self.assertEqual((0, True), (code, data['ok']), result.stderr + result.stdout)
        self.assertTrue((self.p / SKELETON).is_file())
        self.assertFalse((self.p / OLD_LOCK).exists())
        recorded = json.loads((self.p / SKELETON).read_text())
        self.assertEqual(2, recorded['schema_version'])
        self.assertTrue(recorded['files'])

    def test_skeleton_is_not_started_before_configuration(self):
        self.language()
        _, data, _ = self.status()
        self.assertEqual('configure', data['next'])  # configure outranks skeleton
        self.assertFalse((self.p / SKELETON).exists())

    def test_configured_and_in_sync_is_ready(self):
        self.language(); self.evidence()
        self.box.call('setup', '--plugin', PLUGIN)
        _, data, _ = self.status()
        self.assertEqual('ready', data['next'])


if __name__ == '__main__':
    unittest.main()
