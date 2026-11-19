from tests.support.local_plugins_fixture import (
    importlib, json, os, Path, shutil, subprocess, tempfile, unittest, patch, ROOT, spec, engine, SharedLocalTestsFixture
)

class SharedLocalTests(SharedLocalTestsFixture, unittest.TestCase):
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


    def test_branch_switch_reuses_catalog_and_snapshots_current_uncommitted_checkout(self):
        def git(*args):
            return subprocess.run(['git','-C',str(self.coach),*args],check=True,capture_output=True)
        git('init','-q','--initial-branch=main')
        git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
        git('add','--','plugin.json','skills');git('commit','-qm','Fictional base')
        first=engine.install_local('codex',dry_run=True,root=self.root)
        git('switch','-c','exercise-local-checkout')
        skill=self.coach/'skills/example/SKILL.md'
        skill.write_text(skill.read_text()+'\nFictional feature branch content.\n')
        git('add','--','skills');git('commit','-qm','Fictional branch fixture')
        skill.write_text(skill.read_text()+'\nUncommitted local instructions.\n')
        changed=engine.install_local('codex',update=True,dry_run=True,root=self.root)
        self.assertEqual(first['marketplace'],changed['marketplace'])
        self.assertEqual(first['path'],changed['path'])
        self.assertNotEqual(first['plugins']['interview-coach']['version'],changed['plugins']['interview-coach']['version'])
        self.assertEqual(skill.read_bytes(),(Path(changed['path'])/'plugins/interview-coach/skills/example/SKILL.md').read_bytes())
        # Discard only this test fixture's edit to exercise a second branch switch.
        git('restore','--','skills/example/SKILL.md');git('switch','main')
        restored=engine.install_local('codex',update=True,dry_run=True,root=self.root)
        self.assertEqual(first['plugins']['interview-coach']['version'],restored['plugins']['interview-coach']['version'])
        self.assertEqual(first['path'],restored['path'])


    def test_example_json_is_never_runtime_configuration(self):
        (self.root/'local-marketplace.example.json').write_text('{broken optional example')
        self.assertEqual('shared-fixture-dev',engine.install_local('codex',dry_run=True,root=self.root)['marketplace'])
        (self.root/'.local/marketplace.json').unlink()
        with patch.object(engine.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'Missing local checkout'):
                engine.install_local('codex',root=self.root)
            run.assert_not_called()
