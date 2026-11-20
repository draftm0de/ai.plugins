"""A plugin whose name or display name differs from its marketplace catalog entry is reported before installation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'Makefile').is_file())
SPEC = importlib.util.spec_from_file_location('catalog_verifier', ROOT/'skills/_shared/scripts/verify.py')
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)
REPO = 'https://github.com/example/ai.plugin.demo'


class CatalogIdentityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.plugin, self.market = (base/'plugin').resolve(), (base/'market').resolve()
        for folder in (self.plugin/'.local', self.market/'.local'):
            folder.mkdir(parents=True)
        self.write(self.plugin/'plugin.json', name='demo-manager', repository=REPO,
                   extensions={'com.openai': {'interface': {'displayName': 'Demo Manager'}}})
        self.write(self.plugin/'.local/marketplace.json', marketplace=str(self.market))
        self.write(self.market/'.local/marketplace.json', sources={'demo-manager': str(self.plugin)})
        verify.marketplace = lambda root: {}          # catalog structure is not under test here

    @staticmethod
    def write(path, **data):
        path.write_text(json.dumps(data))

    def catalog(self, name, display):
        self.write(self.market/'marketplace.json', plugins=[{'name': name, 'displayName': display, 'repository': REPO + '.git'}])

    def test_matching_entry_is_complete(self):
        self.catalog('demo-manager', 'Demo Manager')
        self.assertTrue(verify.local_configuration(self.plugin, 'plugin')['complete'])

    def test_renamed_plugin_with_stale_catalog_name_names_the_catalog_as_the_place_to_fix(self):
        self.catalog('demo', 'Demo Manager')
        result = verify.local_configuration(self.plugin, 'plugin')
        self.assertFalse(result['complete'])
        self.assertIn("catalog entry 'demo'", result['findings'][0])
        self.assertIn('does not own the catalog', result['findings'][0])

    def test_stale_display_name_is_reported(self):
        self.catalog('demo-manager', 'Demo')
        self.assertFalse(verify.local_configuration(self.plugin, 'plugin')['complete'])


if __name__ == '__main__':
    unittest.main()
