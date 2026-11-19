from tests.support.marketplace_fixture import (
    importlib, json, os, shutil, subprocess, Path, tempfile, unittest, ROOT, spec, engine, MarketplaceTestsFixture
)

class MarketplaceTests(MarketplaceTestsFixture, unittest.TestCase):
    def test_obsolete_versions_rejected_before_catalog_writes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = json.loads((ROOT/'marketplace.json').read_text())
            config['plugins'] = [config['plugins'][1]]
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

    def test_catalogs_point_to_local_manager(self):
        self.assertTrue(engine.sync(check=True)['valid'])
        for catalog in engine.expected().values():
            self.assertEqual('draftmode-ai-plugins',catalog['name'])
            self.assertEqual('plugin-manager',catalog['plugins'][0]['name'])
        self.assertEqual('Plugin Manager', engine.expected()['.claude-plugin/marketplace.json']['plugins'][0]['displayName'])
        manifest=json.loads((ROOT/'plugins/plugin-manager/.claude-plugin/plugin.json').read_text())
        self.assertEqual('Plugin Manager', manifest['displayName'])
        source=engine.expected()['.agents/plugins/marketplace.json']['plugins'][0]['source']
        self.assertEqual({'source':'local','path':'./plugins/plugin-manager'},source)
        plugin=ROOT/'plugins/plugin-manager'
        self.assertTrue((plugin/'skills/_shared/WORKFLOWS.md').is_file())
        self.assertFalse((plugin/'.claude-plugin/marketplace.json').exists())


    def test_external_coach_entry_has_remote_source_and_no_version_pin(self):
        for catalog in engine.expected().values():
            entries = {entry['name']: entry for entry in catalog['plugins']}
            self.assertIn('plugin-manager', entries)
            self.assertIn('interview-coach', entries)
            source=entries['interview-coach']['source']
            self.assertEqual({'source':'url','url':'https://github.com/draftm0de/ai.plugin.interview-coach.git'},source)
            self.assertNotIn('version', entries['interview-coach'])
        coach = next(entry for entry in engine.expected()['.claude-plugin/marketplace.json']['plugins'] if entry['name'] == 'interview-coach')
        self.assertEqual('Interview Coach', coach['displayName'])

    def test_additional_external_plugin_is_in_both_catalogs(self):
        config = json.loads((ROOT/'marketplace.json').read_text())
        extra = {'name': 'fictional-extra', 'displayName': 'Fictional Extra',
                 'description': 'Fictional test plugin', 'repository': 'https://github.com/example/fictional-extra.git'}
        config['plugins'].insert(0, extra)
        for catalog in engine.expected(config=config).values():
            names = [entry['name'] for entry in catalog['plugins']]
            self.assertEqual(1, names.count('fictional-extra'))
            self.assertIn('interview-coach', names)
            entry = next(entry for entry in catalog['plugins'] if entry['name'] == 'fictional-extra')
            self.assertEqual({'source': 'url', 'url': extra['repository']}, entry['source'])


    def test_ambiguous_or_credentialed_remote_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=json.loads((ROOT/'marketplace.json').read_text())
            entry=config['plugins'][1]
            config['plugins']=[entry]
            for change in ({'path':'./plugins/coach'}, {'repository':'https://token@github.com/example/repo.git'}):
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


    def test_canonical_standalone_runtime_copies_match(self):
        skill=ROOT/'plugins/plugin-manager/skills/_shared'
        for name in ('marketplace.py','local_plugins.py','plugin_payload.py','verify.py'):
            self.assertEqual((skill/'templates/marketplace/scripts'/name).read_bytes(),(ROOT/'scripts'/name).read_bytes(),name)
        self.assertEqual((skill/'templates/plugin/scripts/plugin.py').read_bytes(),(ROOT/'scripts/plugin_payload.py').read_bytes())
        self.assertEqual((skill/'scripts/verify.py').read_bytes(),(ROOT/'scripts/verify.py').read_bytes())
        for kind in ('plugin','marketplace'):
            self.assertEqual((skill/'references/prerequisites.md').read_bytes(),(skill/'templates'/kind/'docs/prerequisites.md').read_bytes())
