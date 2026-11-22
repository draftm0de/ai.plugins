"""Starter structural checks only; add tests for the actual product behavior."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StructureTests(unittest.TestCase):
    def test_plugin_identity_and_skill_entrypoint(self):
        portable = json.loads((ROOT / 'plugin.json').read_text())
        self.assertNotIn('version', portable)
        for name in ('.claude-plugin/plugin.json',):
            self.assertTrue((ROOT / name).is_file())
        self.assertTrue(list((ROOT / 'skills').glob('*/SKILL.md')))

    def test_no_plugin_catalogs(self):
        for name in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
            self.assertFalse((ROOT / name).exists())
