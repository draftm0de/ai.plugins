"""R24: modify changes what a plugin or marketplace states about itself; fictional repositories only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests.support.workflow_fixture import WorkflowFixture, flow, ROOT

MODIFY = ROOT / 'skills/modify/scripts/modify.py'
CONFIG = '.project/plugins/plugin-manager/config.json'
LOCAL = '.project/plugins/plugin-manager/local.json'


def load_modify():
    return flow.module(MODIFY, 'modify_under_test')


def snapshot(*roots):
    return {str(p): p.read_bytes() for base in roots for p in sorted(base.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(base).parts}


def data(path):
    return json.loads(Path(path).read_text())


class ModifyBase(WorkflowFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.modify = load_modify()
        self.create_configured()

    def entry(self, name='new-plugin'):
        return next(e for e in data(self.market / 'marketplace.json')['plugins'] if e.get('name') == name)

    def record_market(self):
        helper = flow.state_helper()
        result = helper.record(helper.Context('plugin-manager'), str(self.market), 'marketplace', 'fictional-market')
        self.assertTrue(result['ok'], result)


class PluginModifyTests(ModifyBase):
    def test_description_and_display_name_follow_into_the_manifests_and_the_marketplace_entry(self):
        result = self.modify.modify(self.plugin, display_name='Changed Plugin', description='A changed fictional capability')
        self.assertEqual(('modify', 'plugin', False, False), (result['action'], result['kind'], result['published'], result['catalog_entry_remains']))
        manifest = data(self.plugin / 'plugin.json')
        self.assertEqual('A changed fictional capability', manifest['description'])
        self.assertEqual('Changed Plugin', manifest['extensions']['com.openai']['interface']['displayName'])
        self.assertEqual('new-plugin', manifest['name'])
        self.assertEqual({'displayName': 'Changed Plugin', 'description': 'A changed fictional capability'},
                         {k: self.entry()[k] for k in ('displayName', 'description')})
        self.assertEqual('A changed fictional capability', data(self.plugin / '.claude-plugin/plugin.json')['description'])
        flow.module(ROOT / 'skills/_shared/scripts/verify.py', 'trusted_verify').marketplace(self.market)  # catalogs still valid
        self.assertTrue(result['changed'])

    def test_rename_follows_name_artifact_entry_and_local_mapping_but_keeps_the_repository(self):
        repository = self.entry()['repository']
        result = self.modify.modify(self.plugin, name='renamed-plugin')
        self.assertEqual(('renamed-plugin', 'renamed-plugin'), (data(self.plugin / 'plugin.json')['name'], data(self.plugin / CONFIG)['artifact']))
        self.assertEqual('renamed-plugin', data(self.plugin / '.claude-plugin/plugin.json')['name'])
        names = [e.get('name') for e in data(self.market / 'marketplace.json')['plugins']]
        self.assertIn('renamed-plugin', names)
        self.assertNotIn('new-plugin', names)
        self.assertEqual(repository, self.entry('renamed-plugin')['repository'])
        sources = data(self.market / '.local/marketplace.json')['sources']
        self.assertEqual(['renamed-plugin'], list(sources))
        self.assertEqual(os.path.relpath(self.plugin, self.market), sources['renamed-plugin'])
        self.assertEqual('new-plugin', result['from']['name'])
        self.assertEqual('renamed-plugin', result['to']['name'])
        self.assertTrue(any('/plugin-manager:docs' in note for note in result['follow_up']))

    def test_a_dry_run_lists_the_consequences_and_writes_nothing(self):
        before = snapshot(self.plugin, self.market)
        result = self.modify.modify(self.plugin, name='renamed-plugin', dry_run=True)
        self.assertEqual((True, []), (result['dry_run'], result['changed']))
        names = {Path(path).name for path in result['would_change']}
        self.assertTrue({'plugin.json', 'config.json', 'marketplace.json'} <= names, names)
        self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_same_values_change_nothing(self):
        before = snapshot(self.plugin, self.market)
        result = self.modify.modify(self.plugin, description='Fictional acceptance capability', display_name='Fictional Plugin')
        self.assertEqual(([], False), (result['changed'], result['catalog_entry_remains']))
        self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_unavailable_marketplace_reports_the_remaining_catalog_entry_and_leaves_it_alone(self):
        (self.plugin / LOCAL).unlink()
        market_before = snapshot(self.market)
        result = self.modify.modify(self.plugin, description='Changed while the marketplace is away')
        self.assertTrue(result['catalog_entry_remains'])
        self.assertEqual('Changed while the marketplace is away', data(self.plugin / 'plugin.json')['description'])
        self.assertEqual(market_before, snapshot(self.market))

    def test_invalid_values_and_conflicts_are_refused_before_any_write(self):
        taken = data(self.market / 'marketplace.json')
        taken['plugins'].append({'name': 'taken-name', 'displayName': 'Taken', 'description': 'Another plugin',
                                 'repository': 'https://github.com/example/another.git'})
        (self.market / 'marketplace.json').write_text(json.dumps(taken, indent=2) + '\n')
        before = snapshot(self.plugin, self.market)
        for values in ({'name': 'Not Kebab'}, {'name': ''}, {'display_name': '  '}, {'description': ''}, {'name': 'taken-name'}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.modify.modify(self.plugin, **values)
            self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_an_unconfigured_workpackage_is_refused(self):
        other = self.repo('other-plugin')
        with self.assertRaisesRegex(ValueError, 'Configure first'):
            self.modify.modify(other, description='No evidence yet')


class MarketplaceModifyTests(ModifyBase):
    def test_rename_changes_the_catalogs_and_evidence_and_lists_but_never_touches_the_plugins(self):
        self.record_market()
        plugin_before = snapshot(self.plugin)
        result = self.modify.modify(self.market, name='renamed-market', display_name='Renamed Market')
        self.assertEqual(('modify', 'marketplace', False), (result['action'], result['kind'], result['published']))
        config = data(self.market / 'marketplace.json')
        self.assertEqual(('renamed-market', 'Renamed Market'), (config['name'], config['displayName']))
        self.assertEqual('renamed-market', data(self.market / '.claude-plugin/marketplace.json')['name'])
        self.assertEqual('renamed-market', data(self.market / CONFIG)['artifact'])
        self.assertEqual([{'name': 'new-plugin', 'path': os.path.relpath(self.plugin, self.market)}], result['affected_plugins'])
        self.assertEqual(plugin_before, snapshot(self.plugin))

    def test_a_description_is_not_a_marketplace_field(self):
        self.record_market()
        before = snapshot(self.market)
        with self.assertRaises(ValueError):
            self.modify.modify(self.market, description='Marketplaces have none')
        self.assertEqual(before, snapshot(self.market))

    def test_a_plugin_takes_the_new_marketplace_name_through_associate_without_catalog_changes(self):
        self.record_market()
        self.modify.modify(self.market, name='renamed-market')
        before_market = snapshot(self.market)
        result = flow.associate(self.plugin, self.market)
        self.assertEqual('renamed-market', data(self.plugin / CONFIG)['marketplace']['name'])
        self.assertEqual(before_market, snapshot(self.market))  # identity update only: no entry, no catalog
        self.assertFalse(result['old_catalog_entry_remains'])
        self.assertTrue(any(path.endswith('config.json') for path in result['changed']))


class ModifyCommandLineTests(ModifyBase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-I', str(MODIFY), *args], capture_output=True, text=True, env={'PATH': os.environ['PATH']})  # git is a documented prerequisite

    def test_success_prints_the_answer_and_exits_zero(self):
        result = self.run_cli('--root', str(self.plugin), '--description', 'Changed through the command line')
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        answer = json.loads(result.stdout)
        self.assertEqual(('modify', 'plugin', False), (answer['action'], answer['kind'], answer['published']))
        self.assertEqual('Changed through the command line', data(self.plugin / 'plugin.json')['description'])

    def test_a_refusal_prints_the_reason_and_exits_one_without_writes(self):
        before = snapshot(self.plugin, self.market)
        result = self.run_cli('--root', str(self.plugin), '--name', 'Not Kebab')
        self.assertEqual(1, result.returncode)
        self.assertIn('ERROR: The technical name must be lowercase kebab-case', result.stderr)
        self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_no_value_is_an_invalid_call(self):
        self.assertEqual(2, self.run_cli('--root', str(self.plugin)).returncode)


if __name__ == '__main__':
    unittest.main()
