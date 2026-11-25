from tests.support.marketplace_fixture import (
    importlib, json, os, shutil, subprocess, Path, tempfile, unittest, ROOT, spec, engine, MarketplaceTestsFixture
)

def external_entry():
    return {'name': 'fictional-external', 'displayName': 'Fictional External',
            'description': 'Fictional external plugin', 'repository': 'https://github.com/example/fictional-external.git'}


class MarketplaceTests(MarketplaceTestsFixture, unittest.TestCase):
    def test_obsolete_versions_rejected_before_catalog_writes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = json.loads((ROOT/'marketplace.json').read_text())
            config['plugins'] = [external_entry()]
            for entry in (config, config['plugins'][0]):
                entry['version'] = '1.0.0'
                (root/'marketplace.json').write_text(json.dumps(config))
                for name in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
                    p = root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('protected')
                before = {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with patch.object(engine, 'ROOT', root), self.assertRaisesRegex(ValueError, 'version'):
                    engine.sync()
                self.assertEqual(before, {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()})
                del entry['version']

    def test_external_entry_has_remote_source_and_no_version_pin(self):
        config = json.loads((ROOT/'marketplace.json').read_text())
        extra = external_entry()
        config['plugins'].append(extra)
        catalogs = engine.expected(config=config)
        for catalog in catalogs.values():
            entries = {entry['name']: entry for entry in catalog['plugins']}
            self.assertEqual({'source':'url','url':'https://github.com/draftm0de/ai.plugin.plugin-manager.git'}, entries['plugin-manager']['source'])
            self.assertIn(extra['name'], entries)
            self.assertEqual({'source':'url','url':extra['repository']}, entries[extra['name']]['source'])
            self.assertNotIn('version', entries[extra['name']])
        external = next(entry for entry in catalogs['.claude-plugin/marketplace.json']['plugins'] if entry['name'] == extra['name'])
        self.assertEqual('Fictional External', external['displayName'])

    def test_additional_external_plugin_is_in_both_catalogs(self):
        config = json.loads((ROOT/'marketplace.json').read_text())
        extra = {'name': 'fictional-extra', 'displayName': 'Fictional Extra',
                 'description': 'Fictional test plugin', 'repository': 'https://github.com/example/fictional-extra.git'}
        config['plugins'].insert(0, extra)
        for catalog in engine.expected(config=config).values():
            names = [entry['name'] for entry in catalog['plugins']]
            self.assertEqual(1, names.count('fictional-extra'))
            self.assertIn('plugin-manager', names)
            entry = next(entry for entry in catalog['plugins'] if entry['name'] == 'fictional-extra')
            self.assertEqual({'source': 'url', 'url': extra['repository']}, entry['source'])


    def test_ambiguous_or_credentialed_remote_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=json.loads((ROOT/'marketplace.json').read_text())
            entry=external_entry()
            config['plugins']=[entry]
            for change in ({'path':'./plugins/fictional'}, {'repository':'https://token@github.com/example/repo.git'}):
                original=dict(entry);entry.update(change)
                (root/'marketplace.json').write_text(json.dumps(config))
                with self.assertRaises(ValueError):engine.expected(root)
                entry.clear();entry.update(original)


    def test_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=json.loads((ROOT/'marketplace.json').read_text())
            config['plugins']=[{'path':'./plugins/../../external'}]
            (root/'marketplace.json').write_text(json.dumps(config))
            with self.assertRaises(ValueError):engine.expected(root)


