from tests.support.shared_installer_fixture import (
    importlib, json, os, Path, shutil, subprocess, sys, tempfile, unittest, patch, attach, ROOT, spec, engine, SharedInstallerTestsFixture, LocalDevelopmentTestsFixture
)

class SharedInstallerTests(SharedInstallerTestsFixture, unittest.TestCase):
    def test_whitespace_description_rejected_before_snapshot_replacement(self):
        self.invoke('make','-s','install-local','DRY_RUN=1')
        before = {str(p):p.read_bytes() for p in (self.market/'dist').rglob('*') if p.is_file()}
        self.manifest['description']='   ';self.write_manifest()
        result=subprocess.run(['make','-s','install-local','DRY_RUN=1'],cwd=self.root,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('description is required',result.stderr)
        self.assertEqual(before,{str(p):p.read_bytes() for p in (self.market/'dist').rglob('*') if p.is_file()})

    def test_parallel_host_layout_preserves_existing_snapshots(self):
        self.invoke('make','-s','install-local','DRY_RUN=1')
        before = {str(p):p.read_bytes() for p in (self.market/'dist').rglob('*') if p.is_file()}
        self.assertTrue(before)
        for obsolete in ('.claude/skills','.agents/skills'):
            path = self.root/obsolete; path.mkdir(parents=True)
            result = subprocess.run(['make','-s','install-local','DRY_RUN=1'],cwd=self.root,capture_output=True,text=True)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('Unsupported host-local',result.stderr)
            self.assertEqual(before, {str(p):p.read_bytes() for p in (self.market/'dist').rglob('*') if p.is_file()})
            path.rmdir()

    def test_snapshot_rejects_version_and_custom_skill_root(self):
        for change in ('version', 'skillRoot'):
            original = json.loads(json.dumps(self.manifest))
            if change == 'version':
                self.manifest['version'] = '1.0.0'
            else:
                shutil.copytree(self.root/'skills', self.root/'custom/skills')
                self.manifest['extensions']['io.zyris.distribution']['skillRoot'] = 'custom/skills'
            self.write_manifest()
            with patch.object(engine, 'ROOT', self.root), self.assertRaises(ValueError):
                engine.payload()
            self.manifest = original
            self.write_manifest()

    def test_embedded_manager_never_discovers_parent_marketplace(self):
        embedded = self.root/'parent/plugins/plugin-manager'
        embedded.mkdir(parents=True)
        (embedded.parent.parent/'marketplace.json').write_text('{"name":"draftmode-ai-plugins"}')
        with patch.object(engine, 'ROOT', embedded), self.assertRaisesRegex(ValueError, 'unavailable'):
            engine.install_local('claude', dry_run=True)
        self.assertFalse((embedded.parent.parent/'dist').exists())

    def test_removed_commands_fail_without_creating_outputs(self):
        for command in ('package', 'install', 'update'):
            result = subprocess.run(['make', '-s', command], cwd=self.root, capture_output=True)
            self.assertNotEqual(0, result.returncode, command)
        for command in ('build', 'install', 'update'):
            for prefix in ([sys.executable, 'scripts/plugin.py'],):
                result = subprocess.run(prefix + [command], cwd=self.root, capture_output=True)
                self.assertEqual(2, result.returncode, command)
        self.assertFalse((self.market/'dist').exists())
        self.assertFalse((self.root/'plugin.mk').exists())


    def test_make_metadata_check_detects_and_sync_repairs_drift(self):
        catalog = self.root/'.claude-plugin/plugin.json'
        catalog.write_text('{}')
        result = subprocess.run(['make', '-s', 'check-plugin'], cwd=self.root, capture_output=True)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('{}', catalog.read_text())
        self.invoke('make', '-s', 'sync-plugin')
        self.invoke('make', '-s', 'check-plugin')
        self.assertNotIn('version', json.loads(catalog.read_text()))


    def test_different_marketplace_name_is_rejected(self):
        self.manifest['extensions']['io.zyris.distribution']['marketplace'] = 'another-marketplace'
        self.write_manifest()
        with patch.object(engine, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Unsupported distribution'):
                engine.configuration()
            with self.assertRaisesRegex(ValueError, 'Unsupported distribution'):
                engine.repository_files(self.manifest)


    def test_extra_file_mapping_cannot_ship_local_outputs_or_bytecode(self):
        for relative in ('.local/marketplace.json', '.git/config', '.tmp/report.txt', 'dist/old.zip', '.idea/workspace.xml',
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


    def test_arbitrary_manifest_drives_both_entry_points(self):
        first=json.loads(self.invoke(sys.executable,'scripts/plugin.py','install-local','--target','claude','--dry-run').stdout)
        second=self.invoke('make','-s','install-local','TARGET=claude','DRY_RUN=1')
        self.assertEqual(first,json.loads(second.stdout))
        self.assertEqual(first['path'],first['commands'][0][4])
        self.assertEqual('fictional-product@fictional-market-dev',first['commands'][1][3])
        self.assertEqual('install',first['commands'][1][2])
        catalog=json.loads((self.market/'marketplace.json').read_text())
        self.assertEqual('fictional-market',catalog['name'])
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
            result=subprocess.run([sys.executable,'scripts/plugin.py',*args],cwd=self.root,env=env,capture_output=True)
            self.assertEqual(2,result.returncode)
        self.invoke(sys.executable,'scripts/plugin.py','install-local','--target','claude','--dry-run')
        self.assertEqual('preserve',(legacy/'SKILL.md').read_text())
        self.assertEqual('fictional-progress',(private/'state.json').read_text())



    def test_codex_missing_cli_and_failed_registration_never_report_success(self):
        with patch.object(engine,'ROOT',self.root), patch.object(engine.shutil,'which',return_value=None), patch.object(engine.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError, 'codex CLI not found'):engine.install_local('codex')
            run.assert_not_called()
        with patch.object(engine,'ROOT',self.root), patch.object(engine.shutil,'which',return_value='codex'), patch.object(engine.subprocess,'run',side_effect=subprocess.CalledProcessError(7,['codex'])) as run:
            with self.assertRaises(subprocess.CalledProcessError):engine.install_local('codex')
            self.assertEqual(1,run.call_count)


class LocalDevelopmentTests(LocalDevelopmentTestsFixture, unittest.TestCase):
    def test_local_snapshot_is_separate_and_includes_uncommitted_changes(self):
        with patch.object(engine, 'ROOT', self.root), patch.object(engine.subprocess, 'run') as run:
            first = engine.install_local('codex', dry_run=True)
            run.assert_not_called()
            self.assertEqual('fictional-market-dev', first['marketplace'])
            self.assertNotIn(self.manifest['repository'], str(first['commands']))
            self.assertFalse(first['published'])
            self.assertFalse(list((self.market/'dist/local-development').glob('*.zip')))
            skill=self.root/'skills/fictional-skill/SKILL.md'
            skill.write_text(skill.read_text()+'\nUncommitted fictional change.\n')
            second=engine.install_local('codex',dry_run=True)
            self.assertNotEqual(first['plugins']['fictional-product']['version'],second['plugins']['fictional-product']['version'])
            copied=Path(second['path'])/'plugins/fictional-product/skills/fictional-skill/SKILL.md'
            self.assertEqual(skill.read_bytes(),copied.read_bytes())


    def test_local_install_needs_no_remote_and_never_writes_host_cache_directly(self):
        # Local installation never fetches the configured GitHub source.
        with patch.object(engine,'ROOT',self.root), patch.object(engine.subprocess,'run') as run:
            result=engine.install_local('claude',dry_run=True)
            run.assert_not_called()
            self.assertEqual(['claude','plugin','install'],result['commands'][1][:3])
            self.assertTrue(Path(result['path']).is_relative_to(self.market/'dist'))


    def test_local_install_preserves_foreign_output(self):
        output=self.market/'dist/local-development/codex-marketplace'
        output.mkdir(parents=True);(output/'keep.txt').write_text('Fictional unrelated file')
        with patch.object(engine,'ROOT',self.root), self.assertRaisesRegex(ValueError,'unowned'):
            engine.install_local('codex',dry_run=True)
        self.assertEqual('Fictional unrelated file',(output/'keep.txt').read_text())
