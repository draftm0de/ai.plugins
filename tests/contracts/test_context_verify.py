import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
HELPER=ROOT/'plugins/plugin-manager/skills/_shared/scripts/verify.py'
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
    def test_quoted_skeleton_marker_is_not_implementation_status(self):
        plugin = self.root/'plugins/plugin-manager'
        path = plugin/'skills/verify/SKILL.md'; original = path.read_text()
        for quote in ('    <!-- plugin-skeleton: unimplemented -->','```md\n```md\n<!-- plugin-skeleton: unimplemented -->\n```','`<!-- plugin-skeleton: unimplemented -->`','```md\n<!-- plugin-skeleton: unimplemented -->\n```'):
            path.write_text(original+'\n'+quote+'\n')
            self.assertEqual(engine.plugin(plugin)['implementation_status'],'not_assessed')
        path.write_text(original+'\n<!-- plugin-skeleton: unimplemented -->\n')
        self.assertEqual(engine.plugin(plugin)['implementation_status'],'skeleton')

    def test_complete_host_metadata_drift_and_dangling_layout_are_rejected(self):
        plugin = self.root/'plugins/plugin-manager'
        paths = [plugin/'.claude-plugin/plugin.json',self.root/'.claude-plugin/marketplace.json',self.root/'.agents/plugins/marketplace.json']
        for path in paths:
            original = path.read_bytes();value=json.loads(original);value['unexpected']='preserve'
            path.write_text(json.dumps(value));before=path.read_bytes()
            self.assertFalse(engine.verify(plugin if path==paths[0] else self.root)['valid'])
            self.assertEqual(before,path.read_bytes());path.write_bytes(original)
        path = plugin/'plugin.json';value=json.loads(path.read_text());value['keywords']=['changed']
        original=path.read_bytes();path.write_text(json.dumps(value))
        self.assertFalse(engine.verify(plugin)['valid']);path.write_bytes(original)
        old=plugin/'.claude/skills';old.parent.mkdir(exist_ok=True);old.symlink_to(plugin/'missing')
        self.assertFalse(engine.verify(plugin)['valid']);self.assertTrue(old.is_symlink())

    def test_embedded_manager_without_mapping_is_unavailable(self):
        report = engine.verify(self.root/'plugins/plugin-manager')
        self.assertTrue(report['structure_valid'])
        self.assertEqual(report['local_development']['status'], 'unavailable')

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

    def test_missing_or_invalid_local_configuration_does_not_invalidate_structure(self):
        report=engine.verify(self.root)
        self.assertTrue(report['structure_valid'])
        self.assertFalse(report['local_development']['complete'])
        (self.root/'.local').mkdir()
        (self.root/'.local/marketplace.json').write_text('{broken')
        report=engine.verify(self.root)
        self.assertTrue(report['valid'])
        self.assertEqual('unavailable',report['local_development']['status'])

    def test_only_existing_embedded_manager_exception_is_accepted(self):
        config=json.loads((self.root/'marketplace.json').read_text())
        config['name']='another-market'
        (self.root/'marketplace.json').write_text(json.dumps(config))
        for relative in ('.claude-plugin/marketplace.json','.agents/plugins/marketplace.json'):
            path=self.root/relative;data=json.loads(path.read_text());data['name']='another-market';path.write_text(json.dumps(data))
        self.assertFalse(engine.verify(self.root)['valid'])

    def test_codex_catalog_policy_drift_is_rejected(self):
        path=self.root/'.agents/plugins/marketplace.json'
        data=json.loads(path.read_text());data['plugins'][0]['policy']['installation']='UNKNOWN'
        path.write_text(json.dumps(data))
        self.assertFalse(engine.verify(self.root)['valid'])
