from tests.support.shared_installer_fixture import (
    importlib, json, os, Path, shutil, subprocess, sys, tempfile, unittest, patch, attach, ROOT, spec, engine, SharedInstallerTestsFixture, LocalDevelopmentTestsFixture
)

class LocalDevelopmentTests(LocalDevelopmentTestsFixture, unittest.TestCase):
    @unittest.skipUnless(os.environ.get('AI_PLUGIN_TEST_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'), 'Opt-in isolated Claude/Codex local workflow')
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
                    self.assertNotEqual(first['plugins']['fictional-product']['version'],second['plugins']['fictional-product']['version'])
                    cache=(codex_home if host=='codex' else claude_home)/'plugins/cache'/second['marketplace']/'fictional-product'/second['plugins']['fictional-product']['version']/'skills/fictional-skill/SKILL.md'
                    # Claude local sources can be loaded in-place; inspect the recorded source if no cached copy is present.
                    if not cache.exists() and host=='claude':
                        listing=json.loads(subprocess.check_output(['claude','plugin','list','--json']))
                        entry=next(x for x in listing if x['id']=='fictional-product@'+second['marketplace'])
                        cache=Path(entry.get('readFromFolder') or entry['installPath'])/'skills/fictional-skill/SKILL.md'
                    self.assertEqual(skill.read_bytes(),cache.read_bytes())
