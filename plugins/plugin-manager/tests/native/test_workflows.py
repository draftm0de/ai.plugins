from tests.support.workflows_fixture import (
    importlib, json, os, Path, shutil, subprocess, sys, tempfile, unittest, patch, materialize, ROOT, flow, verify, WorkflowFixture, IntegrationWorkflowTestsFixture
)

class IntegrationWorkflowTests(IntegrationWorkflowTestsFixture, unittest.TestCase):
    @unittest.skipUnless(os.environ.get('AI_PLUGIN_TEST_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'),'Opt-in isolated native acceptance')
    def test_native_creation_configuration_install_update(self):
        self.create();existing=self.repo('existing-plugin');self.create(existing);flow.configure(existing,self.market)
        home=self.root/'isolated-host';home.mkdir()
        claude=home/'claude';claude.mkdir();codex=home/'codex';codex.mkdir()
        env=dict(os.environ,HOME=str(home),CLAUDE_CONFIG_DIR=str(claude),CODEX_HOME=str(codex),DISABLE_AUTOUPDATER='1')
        def run(args,cwd=self.market):
            return subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,check=True,timeout=60)
        for host in ('claude','codex'):
            run(['make','-s','install-local','TARGET='+host],self.plugin)
            for path in (self.plugin,existing):
                skill=path/'skills/fictional-skill/SKILL.md';skill.write_text(skill.read_text()+'\nUpdated fictional '+host+' content.\n')
            run(['make','-s','update-local','TARGET='+host],existing)
            if host=='claude':
                listing=json.loads(run(['claude','plugin','list','--json']).stdout)
            for path in (self.plugin,existing):
                name=path.name;selector=name+'@fictional-market-dev'
                if host=='claude':
                    entry=next(e for e in listing if e['id']==selector)
                    loaded=Path(entry.get('readFromFolder') or entry['installPath'])
                else:
                    entry=json.loads(run(['codex','plugin','add',selector,'--json']).stdout)
                    loaded=Path(entry['installedPath'])
                self.assertEqual((path/'skills/fictional-skill/SKILL.md').read_bytes(),(loaded/'skills/fictional-skill/SKILL.md').read_bytes())
