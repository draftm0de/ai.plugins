"""Starter marketplace contracts; add tests for actual product behavior."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]

class MarketplaceStructureTests(unittest.TestCase):
    def test_host_catalog_identity(self):
        manifest = json.loads((ROOT/'marketplace.json').read_text())
        for relative in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
            self.assertEqual(manifest['name'], json.loads((ROOT/relative).read_text())['name'])
