import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_plugins', ROOT/'scripts/local_plugins.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class SharedLocalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'market';self.root.mkdir()
        (self.root/'scripts').mkdir()
        shutil.copy2(ROOT/'scripts/marketplace.py',self.root/'scripts/marketplace.py')
        self.manager=self.root/'plugins/plugin-manager';self.coach=self.root.parent/'coach'
        for path,name in ((self.manager,'plugin-manager'),(self.coach,'interview-coach')):
            (path/'skills/example').mkdir(parents=True)
            (path/'skills/example/SKILL.md').write_text('---\nname: example\ndescription: Fictional test.\n---\n# Example\n')
            (path/'plugin.json').write_text(json.dumps({'name':name,'description':'Fictional test','repository':'https://github.com/example/coach','extensions':{'io.zyris.distribution':{'skillRoot':'skills','catalogs':False}}}))
        (self.manager/'scripts').mkdir()
        shutil.copy2(ROOT/'plugins/plugin-manager/scripts/plugin.py',self.manager/'scripts/plugin.py')
        config={'name':'shared-fixture','displayName':'Shared Fixture','owner':{'name':'Fixture'},'plugins':[{'path':'./plugins/plugin-manager'},{'name':'interview-coach','displayName':'Interview Coach','description':'Fictional test','repository':'https://github.com/example/coach.git'}]}
        (self.root/'marketplace.json').write_text(json.dumps(config))
        (self.root/'.local').mkdir()
        (self.root/'.local/marketplace.json').write_text(json.dumps({'sources':{'interview-coach':str(self.coach)}}))
    def test_both_hosts_use_one_shared_catalog_and_local_only_sources(self):
        with patch.object(engine.subprocess,'run') as run:
            for host in ('claude','codex'):
                result=engine.install_local(host,dry_run=True,root=self.root)
                self.assertEqual('shared-fixture-dev',result['marketplace'])
                self.assertEqual({'plugin-manager','interview-coach'},set(result['plugins']))
                self.assertEqual(3,len(result['commands']))
                self.assertNotIn('https://',str(result['commands']))
                catalog=Path(result['path'])/('.claude-plugin/marketplace.json' if host=='claude' else '.agents/plugins/marketplace.json')
                data=json.loads(catalog.read_text())
                self.assertTrue(all(entry['source'].startswith('./plugins/') if host=='claude' else entry['source']['source']=='local' for entry in data['plugins']))
            run.assert_not_called()
    def test_uncommitted_edits_change_only_affected_plugin_hash(self):
        first=engine.install_local('codex',dry_run=True,root=self.root)
        (self.coach/'skills/example/SKILL.md').write_text('Changed fictional skill')
        second=engine.install_local('codex',update=True,dry_run=True,root=self.root)
        self.assertEqual(first['plugins']['plugin-manager']['version'],second['plugins']['plugin-manager']['version'])
        self.assertNotEqual(first['plugins']['interview-coach']['version'],second['plugins']['interview-coach']['version'])
        copied=Path(second['path'])/'plugins/interview-coach/skills/example/SKILL.md'
        self.assertEqual('Changed fictional skill',copied.read_text())
    def test_missing_or_mismatched_checkout_preserves_previous_snapshot(self):
        first=engine.install_local('claude',dry_run=True,root=self.root)
        path=Path(first['path']);before={str(p):p.read_bytes() for p in path.rglob('*') if p.is_file()}
        (self.root/'.local/marketplace.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Missing local checkout'):engine.install_local('claude',dry_run=True,root=self.root)
        self.assertEqual(before,{str(p):p.read_bytes() for p in path.rglob('*') if p.is_file()})
    def test_foreign_destination_is_not_replaced(self):
        output=self.root/'dist/local-development/claude-marketplace';output.mkdir(parents=True)
        (output/'keep').write_text('preserve')
        with self.assertRaisesRegex(ValueError,'unowned'):engine.install_local('claude',dry_run=True,root=self.root)
        self.assertEqual('preserve',(output/'keep').read_text())
    def test_native_errors_propagate(self):
        with patch.object(engine.shutil,'which',return_value='claude'),patch.object(engine.subprocess,'run',side_effect=subprocess.CalledProcessError(7,['claude'])):
            with self.assertRaises(subprocess.CalledProcessError):engine.install_local('claude',root=self.root)
    @unittest.skipUnless(os.environ.get('ZYRIS_TEST_SHARED_LOCAL')=='1' and shutil.which('claude') and shutil.which('codex'),'Opt-in isolated native shared marketplace')
    def test_native_install_update_both_plugins_without_git(self):
        home=self.root.parent/'home';home.mkdir();(home/'.claude').mkdir();(home/'.codex').mkdir()
        with patch.dict(os.environ,{'HOME':str(home),'CLAUDE_CONFIG_DIR':str(home/'.claude'),'CODEX_HOME':str(home/'.codex'),'DISABLE_AUTOUPDATER':'1'}):
            for host in ('claude','codex'):
                first=engine.install_local(host,root=self.root)
                for source in (self.manager,self.coach):
                    skill=source/'skills/example/SKILL.md';skill.write_text(skill.read_text()+'Updated '+host+'\n')
                second=engine.install_local(host,update=True,root=self.root)
                for name in ('plugin-manager','interview-coach'):
                    self.assertNotEqual(first['plugins'][name]['version'],second['plugins'][name]['version'])
                    cache=home/('.claude' if host=='claude' else '.codex')/'plugins/cache/shared-fixture-dev'/name/second['plugins'][name]['version']/'skills/example/SKILL.md'
                    if host=='claude' and not cache.exists():
                        listing=json.loads(subprocess.check_output(['claude','plugin','list','--json']))
                        entry=next(item for item in listing if item['id']==name+'@shared-fixture-dev')
                        cache=Path(entry.get('readFromFolder') or entry['installPath'])/'skills/example/SKILL.md'
                    self.assertEqual((Path(second['plugins'][name]['source'])/'skills/example/SKILL.md').read_bytes(),cache.read_bytes())
