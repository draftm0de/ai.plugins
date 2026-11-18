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

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'plugin.json').is_file():
    ROOT = ROOT.parent
spec = importlib.util.spec_from_file_location('shared_installer', ROOT / 'scripts/plugin.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class SharedInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        source = self.root / 'skills/fictional-skill'
        source.mkdir(parents=True)
        (source / 'SKILL.md').write_text('---\nname: fictional-skill\ndescription: Fictional test\n---\n# Test')
        self.manifest = {'name':'fictional-product', 'repository':'https://github.com/example/fictional-product','description':'Fictional plugin',
            'extensions': {'io.zyris.distribution':{'skillRoot':'skills'}}}
        self.write_manifest()
        with patch.object(engine, 'ROOT', self.root): engine.repository_metadata()
        for relative in ('scripts/plugin.py','install.sh'):
            target = self.root / relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT / relative,target)
        (self.root / 'Makefile').write_text('PYTHON ?= python3\nTARGET ?= claude\nDRY_RUN ?= 0\n' + (ROOT/'Makefile').read_text().split('# Local development and repository metadata', 1)[1])

    def write_manifest(self):
        (self.root / 'plugin.json').write_text(json.dumps(self.manifest))

    def invoke(self, *args):
        return subprocess.run(args,cwd=self.root,capture_output=True,text=True,check=True)

    def test_removed_commands_fail_without_creating_outputs(self):
        for command in ('package', 'install', 'update'):
            result = subprocess.run(['make', '-s', command], cwd=self.root, capture_output=True)
            self.assertNotEqual(0, result.returncode, command)
        for command in ('build', 'install', 'update'):
            for prefix in (['bash', 'install.sh'], [sys.executable, 'scripts/plugin.py']):
                result = subprocess.run(prefix + [command], cwd=self.root, capture_output=True)
                self.assertEqual(2, result.returncode, command)
        self.assertFalse((self.root/'dist').exists())
        self.assertFalse((self.root/'plugin.mk').exists())

    def test_make_metadata_check_detects_and_sync_repairs_drift(self):
        catalog = self.root/'.claude-plugin/marketplace.json'
        catalog.write_text('{}')
        result = subprocess.run(['make', '-s', 'check-plugin'], cwd=self.root, capture_output=True)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('{}', catalog.read_text())
        self.invoke('make', '-s', 'sync-plugin')
        self.invoke('make', '-s', 'check-plugin')
        self.assertNotIn('version', json.loads(catalog.read_text())['plugins'][0])

    def test_different_marketplace_name_is_rejected(self):
        self.manifest['extensions']['io.zyris.distribution']['marketplace'] = 'another-marketplace'
        self.write_manifest()
        with patch.object(engine, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'must equal'):
                engine.configuration()
            with self.assertRaisesRegex(ValueError, 'must equal'):
                engine.repository_files(self.manifest)

    def test_extra_file_mapping_cannot_ship_local_outputs_or_bytecode(self):
        for relative in ('.tmp/report.txt', 'dist/old.zip', '.idea/workspace.xml',
                         '__pycache__/module.pyc', 'module.pyo', 'module.pyd', '.DS_Store'):
            with self.subTest(relative=relative):
                source = self.root / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text('Fictional local output')
                self.manifest['extensions']['io.zyris.distribution']['files'] = {'assets/leak.txt': relative}
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, 'Generated/local'):
                    engine.configuration(self.root)
        self.manifest['extensions']['io.zyris.distribution']['files'] = {'dist/leak.txt': 'plugin.json'}
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Generated/local'):
            engine.configuration(self.root)

    def test_arbitrary_manifest_drives_both_wrappers_and_update(self):
        first=json.loads(self.invoke('bash','install.sh','install-local','--target','claude','--dry-run').stdout)
        second=self.invoke('make','-s','install-local','TARGET=claude','DRY_RUN=1')
        self.assertEqual(first,json.loads(second.stdout))
        self.assertEqual(first['path'],first['commands'][0][4])
        update=json.loads(self.invoke('bash','install.sh','update-local','--target','claude','--dry-run').stdout)
        self.assertEqual('fictional-product@fictional-product-dev',update['commands'][1][3])
        catalog=json.loads((self.root/'.claude-plugin/marketplace.json').read_text())
        self.assertEqual('fictional-product',catalog['name'])
        self.assertEqual('Fictional plugin',catalog['plugins'][0]['description'])

    def test_native_failure_propagates_and_chatgpt_never_executes_host(self):
        with patch.object(engine,'ROOT',self.root),patch.object(engine.shutil,'which',return_value='claude'),patch.object(engine.subprocess,'run',side_effect=subprocess.CalledProcessError(7,['claude'])) as run:
            with self.assertRaises(subprocess.CalledProcessError):engine.install_local('claude')
            run.reset_mock()
            with self.assertRaises(ValueError):engine.install_local('chatgpt')
            run.assert_not_called()

    def test_manifest_paths_and_identity_are_validated(self):
        with patch.object(engine,'ROOT',self.root):
            for cfg in ({'skillRoot':'../external'},{'skillRoot':'skills','files':{'../escape':'plugin.json'}},{'skillRoot':'skills','files':{'plugin.json':'plugin.json'}}):
                self.manifest['extensions']['io.zyris.distribution']=cfg;self.write_manifest()
                with self.assertRaises(ValueError):engine.payload()
            self.manifest['name']='../bad';self.write_manifest()
            with self.assertRaises(ValueError):engine.configuration()


    def test_existing_skills_and_private_workspace_are_untouched(self):
        private=self.root/'private-training';private.mkdir();(private/'state.json').write_text('fictional-progress')
        legacy=self.root/'home/.agents/skills/fictional-skill';legacy.mkdir(parents=True);(legacy/'SKILL.md').write_text('preserve')
        env=dict(os.environ,HOME=str(self.root/'home'))
        for args in (('claude-chat',),('all',)):
            result=subprocess.run(['bash','install.sh',*args],cwd=self.root,env=env,capture_output=True)
            self.assertEqual(2,result.returncode)
        self.invoke('bash','install.sh','install-local','--target','claude','--dry-run')
        self.assertEqual('preserve',(legacy/'SKILL.md').read_text())
        self.assertEqual('fictional-progress',(private/'state.json').read_text())

    def test_bash_syntax(self):
        self.invoke('bash','-n','install.sh')


    def test_codex_missing_cli_and_failed_registration_never_report_success(self):
        with patch.object(engine,'ROOT',self.root), patch.object(engine.shutil,'which',return_value=None), patch.object(engine.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError, 'codex CLI not found'):engine.install_local('codex')
            run.assert_not_called()
        with patch.object(engine,'ROOT',self.root), patch.object(engine.shutil,'which',return_value='codex'), patch.object(engine.subprocess,'run',side_effect=subprocess.CalledProcessError(7,['codex'])) as run:
            with self.assertRaises(subprocess.CalledProcessError):engine.install_local('codex',update=True)
            self.assertEqual(1,run.call_count)

    @unittest.skipUnless(os.environ.get('ZYRIS_TEST_CODEX_NATIVE') == '1' and shutil.which('codex'), 'Opt-in real Codex CLI integration')
    def test_native_git_update_without_manifest_version(self):
        isolated = self.root / 'isolated-home'; isolated.mkdir()
        codex_home = isolated / '.codex'; codex_home.mkdir()
        env = dict(os.environ, HOME=str(isolated), CODEX_HOME=str(codex_home))
        def invoke(*args):
            return subprocess.run(args, cwd=self.root, env=env, capture_output=True, text=True, check=True, timeout=30)
        invoke('git','init','-q')
        invoke('git','add','--','plugin.json','skills','.claude-plugin','.agents')
        def commit(message): invoke('git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qam',message)
        commit('initial fictional plugin')
        (codex_home/'config.toml').write_text('[marketplaces.fictional-product]\nsource_type = "git"\nsource = '+json.dumps(str(self.root))+'\n')
        invoke('codex','plugin','marketplace','upgrade','fictional-product','--json')
        result=json.loads(invoke('codex','plugin','add','fictional-product@fictional-product','--json').stdout)
        cache=Path(result['installedPath'])/'skills/fictional-skill/SKILL.md'
        skill=self.root/'skills/fictional-skill/SKILL.md'
        self.assertEqual(skill.read_bytes(),cache.read_bytes())
        skill.write_text(skill.read_text()+'\nUpdated fictional instructions.\n');commit('update fictional instructions')
        invoke('codex','plugin','marketplace','upgrade','fictional-product','--json')
        self.assertEqual(skill.read_bytes(),cache.read_bytes())
        self.assertNotIn('version',json.loads((self.root/'plugin.json').read_text()))

class LocalDevelopmentTests(unittest.TestCase):
    setUp = SharedInstallerTests.setUp
    write_manifest = SharedInstallerTests.write_manifest
    def test_local_snapshot_is_separate_and_includes_uncommitted_changes(self):
        with patch.object(engine, 'ROOT', self.root), patch.object(engine.subprocess, 'run') as run:
            first = engine.install_local('codex', dry_run=True)
            run.assert_not_called()
            self.assertEqual('fictional-product-dev', first['marketplace'])
            self.assertNotIn(self.manifest['repository'], str(first['commands']))
            self.assertFalse(first['published'])
            self.assertFalse(list((self.root/'dist/local-development').glob('*.zip')))
            skill=self.root/'skills/fictional-skill/SKILL.md'
            skill.write_text(skill.read_text()+'\nUncommitted fictional change.\n')
            second=engine.install_local('codex',update=True,dry_run=True)
            self.assertNotEqual(first['version'],second['version'])
            copied=Path(second['path'])/'plugins/fictional-product/skills/fictional-skill/SKILL.md'
            self.assertEqual(skill.read_bytes(),copied.read_bytes())

    def test_local_install_needs_no_remote_and_never_writes_host_cache_directly(self):
        self.manifest.pop('repository'); self.write_manifest()
        with patch.object(engine,'ROOT',self.root), patch.object(engine.subprocess,'run') as run:
            result=engine.install_local('claude',dry_run=True)
            run.assert_not_called()
            self.assertEqual(['claude','plugin','install'],result['commands'][1][:3])
            self.assertTrue(Path(result['path']).is_relative_to(self.root/'dist'))

    def test_local_install_preserves_foreign_output(self):
        output=self.root/'dist/local-development/codex-marketplace'
        output.mkdir(parents=True);(output/'keep.txt').write_text('Fictional unrelated file')
        with patch.object(engine,'ROOT',self.root), self.assertRaisesRegex(ValueError,'unowned'):
            engine.install_local('codex',dry_run=True)
        self.assertEqual('Fictional unrelated file',(output/'keep.txt').read_text())

    @unittest.skipUnless(os.environ.get('ZYRIS_TEST_LOCAL_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'), 'Opt-in isolated Claude/Codex local workflow')
    def test_native_local_install_and_update_without_git_or_network(self):
        home=self.root/'isolated-development-home';home.mkdir()
        codex_home=home/'.codex';codex_home.mkdir()
        claude_home=home/'.claude';claude_home.mkdir()
        with patch.dict(os.environ, {'HOME':str(home),'CODEX_HOME':str(codex_home),'CLAUDE_CONFIG_DIR':str(claude_home),'DISABLE_AUTOUPDATER':'1'}), patch.object(engine,'ROOT',self.root):
            for host in ('claude','codex'):
                with self.subTest(host=host):
                    first=engine.install_local(host)
                    skill=self.root/'skills/fictional-skill/SKILL.md'
                    skill.write_text(skill.read_text()+'\nUpdated fictional '+host+' instructions.\n')
                    second=engine.install_local(host,update=True)
                    self.assertNotEqual(first['version'],second['version'])
                    cache=(codex_home if host=='codex' else claude_home)/'plugins/cache'/second['marketplace']/'fictional-product'/second['version']/'skills/fictional-skill/SKILL.md'
                    # Claude local sources can be loaded in-place; inspect the recorded source if no cached copy is present.
                    if not cache.exists() and host=='claude':
                        listing=json.loads(subprocess.check_output(['claude','plugin','list','--json']))
                        entry=next(x for x in listing if x['id']=='fictional-product@'+second['marketplace'])
                        cache=Path(entry.get('readFromFolder') or entry['installPath'])/'skills/fictional-skill/SKILL.md'
                    self.assertEqual(skill.read_bytes(),cache.read_bytes())
