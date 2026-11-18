import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('marketplace',ROOT/'scripts/marketplace.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class MarketplaceTests(unittest.TestCase):
    def test_catalogs_point_to_local_manager(self):
        self.assertTrue(engine.sync(check=True)['valid'])
        for catalog in engine.expected().values():
            self.assertEqual('draftmode-ai-plugins',catalog['name'])
            self.assertEqual('plugin-manager',catalog['plugins'][0]['name'])
        source=engine.expected()['.agents/plugins/marketplace.json']['plugins'][0]['source']
        self.assertEqual({'source':'local','path':'./plugins/plugin-manager'},source)
        plugin=ROOT/'plugins/plugin-manager'
        self.assertTrue((plugin/'skills/plugin-manager/SKILL.md').is_file())
        self.assertFalse((plugin/'.claude-plugin/marketplace.json').exists())
    def test_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=json.loads((ROOT/'marketplace.json').read_text())
            config['plugins']=[{'path':'./plugins/../../external'}]
            (root/'marketplace.json').write_text(json.dumps(config))
            with self.assertRaises(ValueError):engine.expected(root)

    @unittest.skipUnless(os.environ.get('ZYRIS_TEST_LOCAL_NATIVE')=='1' and shutil.which('claude') and shutil.which('codex'), 'Opt-in isolated host import')
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
            self.assertEqual((ROOT/'plugins/plugin-manager/skills/plugin-manager/SKILL.md').read_bytes(),(installed/'skills/plugin-manager/SKILL.md').read_bytes())
