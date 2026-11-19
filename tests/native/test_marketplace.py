from tests.support.marketplace_fixture import (
    importlib, json, os, shutil, subprocess, Path, tempfile, unittest, ROOT, spec, engine, MarketplaceTestsFixture
)

class MarketplaceTests(MarketplaceTestsFixture, unittest.TestCase):
    @unittest.skipUnless(os.environ.get('AI_PLUGIN_TEST_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'), 'Opt-in isolated host import')
    def test_native_marketplace_installs_nested_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            (home/'.codex').mkdir();(home/'.claude').mkdir()
            env=dict(os.environ, HOME=str(home), CODEX_HOME=str(home/'.codex'), CLAUDE_CONFIG_DIR=str(home/'.claude'), DISABLE_AUTOUPDATER='1')
            def run(*args):
                return subprocess.run(args,env=env,cwd=home,capture_output=True,text=True,check=True,timeout=30)
            selector='plugin-manager@draftmode-ai-plugins'
            run('claude','plugin','marketplace','add',str(ROOT))
            run('claude','plugin','install',selector,'--scope','user')
            listing=json.loads(run('claude','plugin','list','--json').stdout)
            self.assertTrue(any(entry['id']==selector for entry in listing))
            run('codex','plugin','marketplace','add',str(ROOT))
            result=json.loads(run('codex','plugin','add',selector,'--json').stdout)
            installed=Path(result['installedPath'])
            self.assertEqual((ROOT/'plugins/plugin-manager/skills/_shared/WORKFLOWS.md').read_bytes(),(installed/'skills/_shared/WORKFLOWS.md').read_bytes())
