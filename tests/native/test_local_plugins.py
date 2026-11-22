from tests.support.local_plugins_fixture import (
    importlib, json, os, Path, shutil, subprocess, tempfile, unittest, patch, ROOT, spec, engine, SharedLocalTestsFixture
)

class SharedLocalTests(SharedLocalTestsFixture, unittest.TestCase):
    @unittest.skipUnless(os.environ.get('AI_PLUGIN_TEST_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'),'Opt-in isolated native shared marketplace')
    def test_native_install_update_both_plugins_without_git(self):
        home=self.root.parent/'home';home.mkdir();(home/'.claude').mkdir();(home/'.codex').mkdir()
        with patch.dict(os.environ,{'HOME':str(home),'CLAUDE_CONFIG_DIR':str(home/'.claude'),'CODEX_HOME':str(home/'.codex'),'DISABLE_AUTOUPDATER':'1'}):
            for host in ('claude','codex'):
                first=engine.install_local(host,root=self.root)
                for source in (self.manager,self.coach):
                    skill=source/'skills/example/SKILL.md';skill.write_text(skill.read_text()+'Updated '+host+'\n')
                second=engine.install_local(host,root=self.root)
                for name in ('plugin-manager','interview-coach'):
                    self.assertNotEqual(first['plugins'][name]['version'],second['plugins'][name]['version'])
                    cache=home/('.claude' if host=='claude' else '.codex')/'plugins/cache/shared-fixture-dev'/name/second['plugins'][name]['version']/'skills/example/SKILL.md'
                    if host=='claude' and not cache.exists():
                        listing=json.loads(subprocess.check_output(['claude','plugin','list','--json']))
                        entry=next(item for item in listing if item['id']==name+'@shared-fixture-dev')
                        cache=Path(entry.get('readFromFolder') or entry['installPath'])/'skills/example/SKILL.md'
                    self.assertEqual((Path(second['plugins'][name]['source'])/'skills/example/SKILL.md').read_bytes(),cache.read_bytes())
