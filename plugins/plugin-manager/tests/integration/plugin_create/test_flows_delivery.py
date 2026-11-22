"""R19: the central entry flow is identical in every generated plugin (common part byte-identical, custom part stubs)."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests.support.workflow_fixture import WorkflowFixture, ROOT

COMMON = ('skills/_shared/scripts/project_setup.py', 'skills/_shared/flows/entry.md', 'skills/_shared/flows/language.md',
          'skills/_shared/flows/skeleton.md', 'skills/_shared/flows/sync.md')


class FlowsDeliveryTests(WorkflowFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.create()

    def run_helper(self, helper, operation, folder, *args):
        result = subprocess.run([sys.executable, '-B', '-I', str(helper), operation, '--target', str(folder), '--plugin', 'new-plugin', *args],
                                capture_output=True, text=True, cwd=self.root, env={'PATH': ''})
        return result.returncode, (json.loads(result.stdout) if result.stdout else None), result

    def test_template_and_manager_copies_are_byte_identical_and_listed_as_common(self):
        listed = json.loads((ROOT / 'skills/_shared/manifests/plugin.sync.json').read_text())['files']
        for relative in COMMON:
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), (ROOT / 'skills/_shared/templates/plugin/sync' / relative).read_bytes())
                self.assertIn(relative, listed)

    def test_generated_plugin_ships_common_part_and_custom_stubs(self):
        for relative in COMMON:
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), (self.plugin / relative).read_bytes())
        skill = (self.plugin / 'skills/new-plugin/SKILL.md').read_text()
        for needle in ('name: new-plugin', '../_shared/flows/entry.md', 'flows/configure.md', '../_shared/references/operator-language.md'):
            self.assertIn(needle, skill)
        configure = (self.plugin / 'skills/new-plugin/flows/configure.md').read_text()
        self.assertTrue(configure.strip())
        self.assertNotIn('plugin-manager', configure + skill)  # no foreign identity, only this plugin's own name
        self.assertEqual({'schema_version': 1, 'product': None, 'derived': []},
                         json.loads((self.plugin / 'skills/_shared/manifests/default.json').read_text()))
        self.assertEqual({'schema_version': 1, 'files': {}, 'removed': []},
                         json.loads((self.plugin / 'skills/_shared/manifests/default.sync.json').read_text()))

    def test_no_manifest_or_template_strays_in_the_generated_repository(self):
        for stray in ('manifest.json', 'manifests', 'templates', 'skills/_shared/templates', 'skills/_shared/manifests/plugin.json',
                      'skills/_shared/manifests/marketplace.json'):
            self.assertFalse((self.plugin / stray).exists(), stray)

    def test_generated_helper_runs_the_whole_flow_in_an_empty_workpackage(self):
        helper = self.plugin / 'skills/_shared/scripts/project_setup.py'
        self.assertEqual((ROOT / 'skills/_shared/scripts/project_setup.py').read_bytes(), helper.read_bytes())
        work = self.root / 'workpackage'; work.mkdir()
        code, data, result = self.run_helper(helper, 'status', work)
        self.assertEqual((0, 'language', 'unconfigured'), (code, data['next'], data['state']), result.stderr + result.stdout)
        code, data, result = self.run_helper(helper, 'language', work, '--language', 'de')
        self.assertEqual((0, True), (code, data['ok']), result.stderr + result.stdout)
        code, data, _ = self.run_helper(helper, 'status', work)
        self.assertEqual(('configure', {'plugin': 'new-plugin', 'configured': False, 'kind': None}), (data['next'], data['configuration']))
        code, data, result = self.run_helper(helper, 'record', work, '--kind', 'default', '--artifact', 'new-plugin')
        self.assertEqual((0, True), (code, data['ok']), result.stderr + result.stdout)
        self.assertTrue((work / '.project/plugins/new-plugin/config.json').is_file())
        code, data, _ = self.run_helper(helper, 'status', work)
        self.assertEqual(('ready', {'plugin': 'new-plugin', 'configured': True, 'kind': 'default'}), (data['next'], data['configuration']))


if __name__ == '__main__':
    unittest.main()
