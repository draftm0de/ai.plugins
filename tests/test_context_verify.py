import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'plugins/plugin-manager/skills/plugin-manager/scripts/verify.py'
spec=importlib.util.spec_from_file_location('context_verify',HELPER)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class ContextVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        for name in ('marketplace.json','.claude-plugin','.agents','plugins'):
            source=ROOT/name;dest=self.root/name
            if source.is_dir():shutil.copytree(source,dest,ignore=shutil.ignore_patterns('dist','.tmp','__pycache__'))
            else:shutil.copy2(source,dest)
    def test_auto_recognizes_each_root_and_mismatches_fail(self):
        plugin=self.root/'plugins/plugin-manager'
        self.assertEqual('marketplace',engine.verify(self.root)['kind'])
        self.assertEqual('plugin',engine.verify(plugin)['kind'])
        self.assertFalse(engine.verify(self.root,'plugin')['valid'])
        self.assertFalse(engine.verify(plugin,'marketplace')['valid'])
    def test_ambiguous_root_requires_explicit_action(self):
        (self.root/'plugin.json').write_text('{}')
        self.assertFalse(engine.verify(self.root)['valid'])
        self.assertTrue(engine.verify(self.root,'marketplace')['valid'])
    def test_verification_is_read_only_and_never_executes_target_code(self):
        path=self.root/'plugins/plugin-manager/scripts/plugin.py'
        path.write_text('raise RuntimeError("Target code must never run")')
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        report=engine.verify(self.root)
        self.assertTrue(report['valid'],report)
        self.assertFalse(report['target_code_executed'])
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_catalog_and_host_manifest_drift_are_errors(self):
        path=self.root/'.agents/plugins/marketplace.json';data=json.loads(path.read_text());data['plugins'].pop();path.write_text(json.dumps(data))
        self.assertFalse(engine.verify(self.root)['valid'])
        path=self.root/'plugins/plugin-manager/.claude-plugin/plugin.json';data=json.loads(path.read_text());data['name']='wrong';path.write_text(json.dumps(data))
        self.assertFalse(engine.verify(path.parent.parent,'plugin')['valid'])
    def test_default_cli_source_is_working_directory_not_installation(self):
        empty=self.root/'empty';empty.mkdir()
        result=subprocess.run([sys.executable,str(HELPER)],cwd=empty,capture_output=True,text=True)
        self.assertEqual(1,result.returncode)
        self.assertEqual(str(empty),json.loads(result.stdout)['source'])
    def test_remote_content_is_explicitly_not_verified(self):
        result=engine.verify(self.root)
        remote=next(p for p in result['plugins'] if p['name']=='interview-coach')
        self.assertFalse(remote['remote_content_verified'])
