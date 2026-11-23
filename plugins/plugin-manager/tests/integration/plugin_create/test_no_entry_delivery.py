"""R23/R16: a generated plugin receives no setup flow and no setup_state.py; it defines its own skills."""
import json
from pathlib import Path
import re
import unittest

from tests.support.workflow_fixture import WorkflowFixture, ROOT

TEMPLATE = ROOT / 'skills/_shared/templates/plugin/sync'
GONE = ('skills/setup/scripts/setup_state.py', 'skills/_shared/flows')
KEPT = ('skills/_shared/scripts/operator_language.py', 'skills/_shared/references/operator-language.md')


class NoEntryDeliveryTests(WorkflowFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.create()

    def test_templates_and_sync_manifest_carry_no_setup_flow(self):
        listed = json.loads((ROOT / 'skills/_shared/manifests/plugin.sync.json').read_text())['files']
        for relative in GONE:
            with self.subTest(path=relative):
                self.assertFalse((TEMPLATE / relative).exists())
                self.assertFalse([path for path in listed if path == relative or path.startswith(relative + '/')])
        for relative in KEPT:
            with self.subTest(path=relative):
                self.assertTrue((TEMPLATE / relative).is_file())
                self.assertIn(relative, listed)

    def test_generated_plugin_has_the_operator_language_block_but_no_setup_flow(self):
        for relative in GONE:
            self.assertFalse((self.plugin / relative).exists(), relative)
        for relative in KEPT:
            self.assertEqual((ROOT / relative).read_bytes(), (self.plugin / relative).read_bytes(), relative)

    def test_generated_skill_stub_references_only_files_that_exist(self):
        skill = self.plugin / 'skills/new-plugin/SKILL.md'
        text = skill.read_text()
        self.assertIn('name: new-plugin', text)
        self.assertNotIn('entry.md', text)
        references = re.findall(r'`(\.\./[^`\s]+)`', text)
        for reference in references:
            self.assertTrue((skill.parent / reference).exists(), reference)

    def test_the_manager_keeps_its_own_helper_and_flows(self):
        self.assertTrue((ROOT / 'skills/setup/scripts/setup_state.py').is_file())
        for name in ('entry', 'language', 'skeleton', 'sync', 'gate'):
            self.assertTrue((ROOT / 'skills/_shared/flows' / (name + '.md')).is_file() or (ROOT / 'skills/setup/flows' / (name + '.md')).is_file(), name)


if __name__ == '__main__':
    unittest.main()
