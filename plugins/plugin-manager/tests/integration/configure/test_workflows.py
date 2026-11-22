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

class ConfigureWorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_ambiguous_json_rejected_before_configure_or_create(self):
        self.create()
        for path in (self.market/'marketplace.json',self.market/'.local/marketplace.json',self.plugin/'.local/marketplace.json'):
            original = path.read_text()
            for injected in ('"custom":1,"custom":2,','"custom":NaN,','"custom":1e999,'):
                path.write_text(original.replace('{','{'+injected,1))
                before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError,'Duplicate JSON|Invalid JSON'):
                    flow.configure(self.plugin,self.market)
                self.assertEqual(before,{str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})
            path.write_text(original)

    def test_unknown_catalog_fields_rejected_without_changes(self):
        self.create()
        path = self.market/'marketplace.json'
        config = json.loads(path.read_text()); config['plugins'][0]['private_annotation'] = 'preserve'
        path.write_text(json.dumps(config))
        before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Unsupported marketplace entry'):
            flow.configure(self.plugin,self.market)
        self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_unsupported_distribution_rejected_before_configuration(self):
        self.create()
        path = self.plugin/'plugin.json'; original = json.loads(path.read_text())
        for invalid in ({'marketplace':'new-plugin'}, {'bogus':1}, {'catalogs':0}, {'files':'invalid'}, {'files':{'../escape':'plugin.json'}}):
            value = json.loads(json.dumps(original)); value['extensions']['io.zyris.distribution'] = invalid
            path.write_text(json.dumps(value))
            before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Unsupported distribution|Distribution files|Unsafe or reserved'):
                flow.configure(self.plugin,self.market)
            self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_other_associations_preserved_explicit_override(self):
        self.create()
        second=self.repo('second-market');flow.marketplace_create(second,'second-market','Second Fictional Market','Fictional Publisher')
        flow.configure(self.plugin,second)
        local=json.loads((self.plugin/'.local/marketplace.json').read_text())
        self.assertEqual({'fictional-market','second-market'},set(local['marketplaces']))
        self.assertEqual('second-market-dev',self.make(self.plugin,'install-local','codex')['marketplace'])
        self.assertEqual('fictional-market-dev',self.make(self.plugin,'install-local','codex',self.market)['marketplace'])
        self.assertEqual('new-plugin',json.loads((self.market/'marketplace.json').read_text())['plugins'][0]['name'])


    def test_configure_existing_minimal_plugin_adds_only_missing_tools(self):
        self.create()
        other=self.repo('bare-plugin')
        for relative in ('plugin.json','.claude-plugin','skills'):
            src=self.plugin/relative;dst=other/relative
            if src.is_dir(): shutil.copytree(src,dst)
            else: shutil.copy2(src,dst)
        manifest=json.loads((other/'plugin.json').read_text())
        manifest['name']='bare-plugin';manifest['repository']='https://github.com/example/bare-plugin'
        (other/'plugin.json').write_bytes(flow.encode(manifest))
        engine=flow.module(flow.SKILL/'templates/plugin/sync/scripts/plugin.py','fixture_engine')
        for path,data in engine.repository_files(manifest).items(): (other/path).write_bytes(flow.encode(data))
        (other/'Makefile').write_text('custom-check:\n\t@echo preserved\n')
        flow.configure(other,self.market)
        self.assertIn('custom-check:',(other/'Makefile').read_text())
        self.assertEqual('fictional-market-dev',self.make(other,'install-local','codex')['marketplace'])


    def test_effective_ignore_conflicts_abort_without_changing_associations(self):
        self.create()
        for target in (self.plugin,self.market):
            with self.subTest(target=target.name):
                ignore=target/'.gitignore';original=ignore.read_bytes()
                ignore.write_text(ignore.read_text()+'\n.local/\n!.local/\n!.local/*.json\n')
                before={str(p):p.read_bytes() for root in (self.plugin,self.market)
                        for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
                with self.assertRaisesRegex(ValueError,'Ineffective Git ignore'):
                    flow.configure(self.plugin,self.market)
                after={str(p):p.read_bytes() for root in (self.plugin,self.market)
                       for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}
                self.assertEqual(before,after)
                ignore.write_bytes(original)


    def test_generated_local_configuration_is_effectively_ignored(self):
        self.create()
        for root in (self.plugin,self.market):
            result=subprocess.run(['git','-C',str(root),'check-ignore','--no-index','--','.local/marketplace.json'],capture_output=True,text=True,check=True)
            self.assertEqual('.local/marketplace.json',result.stdout.strip())
            self.assertNotIn('.local/marketplace.json',subprocess.check_output(['git','-C',str(root),'ls-files','--others','--exclude-standard'],text=True))
