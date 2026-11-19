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
        result=flow.marketplace_create(self.market,config['name'],config['displayName'],config['owner']['name'])
        self.assertEqual(result['changed'],[])

    def test_no_embedded_new_plugins_or_automatic_init(self):
        with self.assertRaisesRegex(ValueError,'separate'):
            flow.plugin_create(self.market/'plugins/new',self.market,self.source)
        result=subprocess.run([sys.executable,'-B',str(flow.SKILL/'scripts/workflows.py'),'init'],cwd=self.root,capture_output=True,text=True,check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'plugin.json').exists())
        result=subprocess.run([sys.executable,'-B',str(flow.SKILL/'scripts/plugin_audit.py'),'init','--source',str(self.source),'--output',str(self.root/'never-created')],cwd=self.root,capture_output=True,text=True,check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'never-created').exists())
