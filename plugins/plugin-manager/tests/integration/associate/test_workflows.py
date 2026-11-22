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

LOCAL = '.project/plugins/plugin-manager/local.json'


class ConfigureWorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_ambiguous_json_rejected_before_configure_or_create(self):
        self.create_configured()
        for path in (self.market/'marketplace.json',self.market/'.local/marketplace.json',self.plugin/LOCAL):
            original = path.read_text()
            for injected in ('"custom":1,"custom":2,','"custom":NaN,','"custom":1e999,'):
                path.write_text(original.replace('{','{'+injected,1))
                before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError,'Duplicate JSON|Invalid JSON'):
                    flow.associate(self.plugin,self.market)
                self.assertEqual(before,{str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})
            path.write_text(original)

    def test_unknown_catalog_fields_rejected_without_changes(self):
        self.create_configured()
        path = self.market/'marketplace.json'
        config = json.loads(path.read_text()); config['plugins'][0]['private_annotation'] = 'preserve'
        path.write_text(json.dumps(config))
        before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Unsupported marketplace entry'):
            flow.associate(self.plugin,self.market)
        self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_unsupported_distribution_rejected_before_configuration(self):
        self.create_configured()
        path = self.plugin/'plugin.json'; original = json.loads(path.read_text())
        for invalid in ({'marketplace':'new-plugin'}, {'bogus':1}, {'catalogs':0}, {'files':'invalid'}, {'files':{'../escape':'plugin.json'}}):
            value = json.loads(json.dumps(original)); value['extensions']['io.zyris.distribution'] = invalid
            path.write_text(json.dumps(value))
            before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Unsupported distribution|Distribution files|Unsafe or reserved'):
                flow.associate(self.plugin,self.market)
            self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_second_marketplace_requires_the_explicit_change(self):
        """R21: a plugin belongs to exactly one marketplace; association_files (creation) never adds a second one."""
        self.create()
        second=self.repo('second-market');flow.create_marketplace(second,'second-market','Second Fictional Market','Fictional Publisher')
        manifest=json.loads((self.plugin/'plugin.json').read_text())
        before={str(p):p.read_bytes() for base in (self.plugin,self.market,second) for p in base.rglob('*') if p.is_file() and '.git' not in p.relative_to(base).parts}
        with self.assertRaisesRegex(ValueError,'use associate to change'):
            flow.association_files(self.plugin,second,manifest)
        self.assertEqual(before,{str(p):p.read_bytes() for base in (self.plugin,self.market,second) for p in base.rglob('*') if p.is_file() and '.git' not in p.relative_to(base).parts})
        self.assertEqual({'schema_version','marketplace_path'},set(json.loads((self.plugin/LOCAL).read_text())))
        self.assertFalse((self.plugin/'.local/marketplace.json').exists())


    def test_effective_ignore_conflicts_abort_without_changing_associations(self):
        self.create_configured()
        conflicts={self.plugin:'\n!/.project/plugins/*/local.json\n',self.market:'\n.local/\n!.local/\n!.local/*.json\n'}
        for target,conflict in conflicts.items():
            with self.subTest(target=target.name):
                ignore=target/'.gitignore';original=ignore.read_bytes()
                ignore.write_text(ignore.read_text()+conflict)
                before={str(p):p.read_bytes() for root in (self.plugin,self.market)
                        for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
                with self.assertRaisesRegex(ValueError,'Ineffective Git ignore'):
                    flow.associate(self.plugin,self.market)
                after={str(p):p.read_bytes() for root in (self.plugin,self.market)
                       for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
                self.assertEqual(before,after)
                ignore.write_bytes(original)


    def test_generated_local_configuration_is_effectively_ignored(self):
        self.create()
        for root,relative in ((self.plugin,LOCAL),(self.market,'.local/marketplace.json')):
            result=subprocess.run(['git','-C',str(root),'check-ignore','--no-index','--',relative],capture_output=True,text=True,check=True)
            self.assertEqual(relative,result.stdout.strip())
            self.assertNotIn(relative,subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard'],text=True))
