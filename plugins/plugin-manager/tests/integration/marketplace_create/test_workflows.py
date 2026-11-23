"""End-to-end creation/configuration using fictional repositories and isolated hosts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests.support.plugin_fixture import materialize

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(ROOT/'skills/_shared/scripts'))
import workflows as flow
import verify

from tests.support.workflow_fixture import WorkflowFixture

class MarketplaceCreateWorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_sync_then_repeated_create_remains_idempotent(self):
        (self.market/'.claude-plugin/marketplace.json').write_text('{}')
        subprocess.run([sys.executable,'-B','scripts/marketplace.py','sync'],cwd=self.market,check=True,capture_output=True)
        config=json.loads((self.market/'marketplace.json').read_text())
        result=flow.create_marketplace(self.market,config['name'],config['displayName'],config['owner']['name'])
        self.assertEqual(result['changed'],[])

    def test_no_embedded_new_plugins_or_automatic_init(self):
        with self.assertRaisesRegex(ValueError,'separate'):
            flow.create_plugin(self.market/'plugins/new',self.market,skeleton=True, license='deferred')
        result=subprocess.run([sys.executable,'-B',str(flow.SKILL/'scripts/workflows.py'),'init'],cwd=self.root,capture_output=True,text=True,check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'plugin.json').exists())
        result=subprocess.run([sys.executable,'-B',str(flow.SKILL/'scripts/plugin_audit.py'),'init','--source',str(self.source),'--output',str(self.root/'never-created')],cwd=self.root,capture_output=True,text=True,check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'never-created').exists())


class MarketplaceFlowAcceptanceTests(unittest.TestCase):
    """R20: marketplace setup inside the central entry, with the real helper and generator."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.market = self.root/'catalog'; self.market.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.market)], check=True)
        subprocess.run(['git', '-C', str(self.market), 'remote', 'add', 'origin', 'https://github.com/example/catalog.git'], check=True)
        self.helper = flow.SKILL.parent/'setup/scripts/setup_state.py'

    def call(self, operation, *args):
        result = subprocess.run([sys.executable, '-B', '-I', str(self.helper), operation, '--target', str(self.market),
                                 '--plugin', 'plugin-manager', *args], capture_output=True, text=True, env={'PATH': ''})
        return result.returncode, json.loads(result.stdout)

    def create(self):
        return flow.create_marketplace(self.market, 'fictional-market', 'Fictional Market', 'Fictional Publisher')

    def test_end_to_end_language_create_record_skeleton_ready(self):
        self.assertEqual('language', self.call('status')[1]['next'])
        self.assertEqual(0, self.call('language', '--language', 'de')[0])
        self.assertEqual('configure', self.call('status')[1]['next'])
        self.assertFalse((self.market/'marketplace.json').exists())
        result = self.create()
        self.assertEqual((False, 'create-marketplace'), (result['published'], result['action']))
        self.assertNotIn('ok', result)
        self.assertEqual('configure', self.call('status')[1]['next'])  # a created product is no evidence
        code, recorded = self.call('record', '--kind', 'marketplace', '--artifact', 'fictional-market')
        self.assertEqual((0, True), (code, recorded['ok']))
        status = self.call('status')[1]
        self.assertEqual(('skeleton', 'marketplace', True), (status['next'], status['state'], status['plugin_configured']))
        code, setup = self.call('setup')
        self.assertEqual((0, True), (code, setup['ok']))
        status = self.call('status')[1]
        self.assertEqual(('ready', True), (status['next'], status['matches_template']))

    def test_repetition_is_idempotent_and_identity_conflict_stops(self):
        self.create()
        self.assertEqual([], self.create()['changed'])
        before = (self.market/'marketplace.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'identity conflicts'):
            flow.create_marketplace(self.market, 'other-market', 'Fictional Market', 'Fictional Publisher')
        self.assertEqual(before, (self.market/'marketplace.json').read_bytes())

    def test_plugin_repository_is_no_marketplace(self):
        (self.market/'plugin.json').write_text('{"name": "demo-plugin"}')
        with self.assertRaisesRegex(ValueError, 'plugin repository'):
            self.create()
        self.assertFalse((self.market/'marketplace.json').exists())

    def test_deviating_synced_file_neither_blocks_nor_changes_and_becomes_a_sync_decision(self):
        (self.market/'scripts').mkdir()
        mine = b'# my own verify\n'
        (self.market/'scripts/verify.py').write_bytes(mine)
        self.create()
        self.assertEqual(mine, (self.market/'scripts/verify.py').read_bytes())
        self.assertTrue((self.market/'scripts/marketplace.py').is_file())  # missing synced files are created
        self.assertEqual(0, self.call('language', '--language', 'de')[0])
        self.assertEqual(0, self.call('record', '--kind', 'marketplace', '--artifact', 'fictional-market')[0])
        self.assertEqual('skeleton', self.call('status')[1]['next'])
        self.assertEqual(0, self.call('setup')[0])
        status = self.call('status')[1]
        self.assertEqual('sync', status['next'])
        self.assertEqual(['scripts/verify.py'], [d['path'] for d in status['sync']['decisions']])

    def test_starter_readmes_name_only_existing_commands(self):
        self.create()
        for name in ('README.md', 'README.en.md'):
            text = (self.market/name).read_text(encoding='utf-8')
            for gone in ('make verify', 'make check-marketplace', 'make sync-marketplace', 'update-local', 'plugin-verify', 'marketplace-verify'):
                self.assertNotIn(gone, text, name)
            for present in ('scripts/verify.py', 'scripts/marketplace.py', 'make install-local'):
                self.assertIn(present, text, name)
