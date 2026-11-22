from tests.support.workflows_fixture import (
    importlib, json, os, Path, shutil, subprocess, sys, tempfile, unittest, patch, materialize, ROOT, flow, verify, WorkflowFixture, IntegrationWorkflowTestsFixture
)

class IntegrationWorkflowTests(IntegrationWorkflowTestsFixture, unittest.TestCase):
    def test_complete_workflow_fresh_clone_and_existing_association(self):
        (self.plugin/'README.md').write_text('Existing project introduction\n')
        (self.plugin/'LICENSE').write_text('Fictional licensing decision preserved\n')
        self.create(license='LicenseRef-Fictional', license_file=self.plugin/'LICENSE')
        existing = self.repo('existing-plugin'); self.create_configured(existing)
        # Remove its association to exercise associate against a pre-existing plugin.
        config = json.loads((self.market/'marketplace.json').read_text())
        config['plugins'] = [e for e in config['plugins'] if e['name'] != 'existing-plugin']
        (self.market/'marketplace.json').write_bytes(flow.encode(config))
        for p,b in flow.catalog_files(self.market,config).items(): p.write_bytes(b)
        flow.associate(existing,self.market)
        self.assertEqual([], flow.associate(existing,self.market)['changed'])
        self.assertEqual('Existing project introduction\n',(self.plugin/'README.md').read_text())
        self.assertEqual('Fictional licensing decision preserved\n',(self.plugin/'LICENSE').read_text())
        for path in (self.market,self.plugin,existing):
            result=verify.verify(path)
            self.assertTrue(result['valid'],result)
            self.assertTrue(result['local_development']['complete'],result)
        for host in ('claude','codex'):
            result=self.make(self.plugin,'install-local',host)
            self.assertEqual({'new-plugin','existing-plugin'},set(result['plugins']))
            skill=existing/'skills/existing-plugin/SKILL.md';skill.write_text(skill.read_text()+'\nFictional change\n')
            update=self.make(existing,'install-local',host)
            self.assertNotEqual(result['plugins']['existing-plugin']['version'],update['plugins']['existing-plugin']['version'])
        shutil.rmtree(self.market/'.local')
        report=verify.verify(self.market)
        self.assertTrue(report['structure_valid'])
        self.assertFalse(report['local_development']['complete'])
        engine=flow.module(self.market/'scripts/local_plugins.py','fixture_local')
        with patch.object(engine.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'Missing local checkout'):engine.install_local('claude',root=self.market)
            run.assert_not_called()


    def test_installed_manager_can_create_without_checkout(self):
        installed=materialize(self.root/'installed')
        market=self.repo('installed-market')
        helper=installed/'skills/_shared/scripts/workflows.py'
        subprocess.run([sys.executable,'-B',str(helper),'marketplace-create','--root',str(market),'--name','installed-market','--display-name','Fictional Installed Market','--owner','Fictional Publisher'],cwd=self.root,check=True,capture_output=True)
        plugin=self.repo('installed-plugin')
        subprocess.run([sys.executable,'-B',str(helper),'plugin-create', '--license', 'deferred','--root',str(plugin),'--marketplace',str(market),'--skeleton','--name','installed-plugin','--display-name','Fictional Plugin','--description','Fictional fixture','--author','Fictional Publisher','--languages','en'],cwd=self.root,check=True,capture_output=True)
        self.assertTrue(verify.verify(plugin)['valid'])
        self.assertFalse((market/'plugins/plugin-manager').exists())
        self.assertEqual('installed-market-dev',self.make(plugin,'install-local','codex')['marketplace'])


    def test_python_snapshots_and_verify_need_neither_make_nor_host_cli(self):
        self.create()
        env=dict(os.environ,PATH='')
        result=subprocess.run([sys.executable,'-B',str(self.plugin/'scripts/plugin.py'),'install-local','--target','codex','--dry-run'],
                              cwd=self.plugin,env=env,check=True,capture_output=True,text=True)
        report=json.loads(result.stdout)
        self.assertFalse(report['executed'])
        self.assertEqual('fictional-market-dev',report['marketplace'])
        result=subprocess.run([sys.executable,'-B',str(self.plugin/'scripts/verify.py'),'--source',str(self.plugin)],
                              cwd=self.plugin,env=env,check=True,capture_output=True,text=True)
        self.assertTrue(json.loads(result.stdout)['structure_valid'])
        self.assertTrue((self.plugin/'docs/prerequisites.md').is_file())
        self.assertTrue((self.market/'docs/prerequisites.md').is_file())
