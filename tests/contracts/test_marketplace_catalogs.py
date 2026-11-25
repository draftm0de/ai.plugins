"""Catalog generation of scripts/marketplace.py. Managed by plugin-manager; fictional data only."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('marketplace', ROOT / 'scripts/marketplace.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
CATALOGS = ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json')


def entry(name='fictional-plugin'):
    return {'name': name, 'displayName': 'Fictional Plugin', 'description': 'Fictional plugin',
            'repository': 'https://github.com/example/' + name + '.git'}


def configuration(*plugins):
    return {'name': 'fictional-market', 'displayName': 'Fictional Market', 'owner': {'name': 'Fixture'},
            'plugins': list(plugins)}


class MarketplaceCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, config):
        (self.root / 'marketplace.json').write_text(json.dumps(config))

    def files(self):
        return {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_each_plugin_has_a_remote_source_in_both_catalogs_and_no_version_pin(self):
        catalogs = engine.expected(config=configuration(entry(), entry('fictional-extra')))
        self.assertEqual(set(CATALOGS), set(catalogs))
        for catalog in catalogs.values():
            self.assertEqual(['fictional-plugin', 'fictional-extra'], [item['name'] for item in catalog['plugins']])
            for item in catalog['plugins']:
                self.assertEqual({'source': 'url', 'url': entry(item['name'])['repository']}, item['source'])
                self.assertNotIn('version', item)
        self.assertEqual('Fictional Plugin', catalogs[CATALOGS[0]]['plugins'][0]['displayName'])

    def test_sync_writes_the_catalogs_and_check_reports_drift(self):
        self.write(configuration(entry()))
        engine.ROOT = self.root
        self.addCleanup(setattr, engine, 'ROOT', ROOT)
        self.assertEqual(list(CATALOGS), engine.sync()['updated'])
        self.assertEqual([], engine.sync(check=True)['updated'])
        (self.root / CATALOGS[0]).write_text('{}')
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'Stale'):
            engine.sync(check=True)
        self.assertEqual(before, self.files())

    def test_a_version_pin_is_rejected_before_catalog_writes(self):
        engine.ROOT = self.root
        self.addCleanup(setattr, engine, 'ROOT', ROOT)
        for relative in CATALOGS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('protected')
        for pinned in ('marketplace', 'plugin'):
            with self.subTest(pinned=pinned):
                config = configuration(entry())
                (config if pinned == 'marketplace' else config['plugins'][0])['version'] = '1.0.0'
                self.write(config)
                before = self.files()
                with self.assertRaisesRegex(ValueError, 'version'):
                    engine.sync()
                self.assertEqual(before, self.files())

    def test_embedded_ambiguous_or_credentialed_entries_are_rejected(self):
        for change in ({'path': './plugins/fictional'}, {'path': './plugins/../../external'},
                       {'repository': 'https://token@github.com/example/repository.git'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                engine.expected(config=configuration(dict(entry(), **change)))
        with self.assertRaises(ValueError):
            engine.expected(config=configuration(entry(), entry()))


if __name__ == '__main__':
    unittest.main()
