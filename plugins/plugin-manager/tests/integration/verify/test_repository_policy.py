import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.support.plugin_fixture import materialize
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(ROOT/'skills/_shared/scripts'))
import repository_policy as policy
import plugin_audit as audit


class RepositoryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root/'repo'
        self.repo.mkdir()
        (self.repo/'.gitignore').write_bytes((ROOT/'skills/_shared/templates/plugin/gitignore.txt').read_bytes())
        subprocess.run(['git','init','--quiet','--template=',str(self.repo)],check=True)

    def test_ignore_rules_work_and_nested_negations_fail_without_mutation(self):
        self.assertEqual(([], []), policy.hygiene(self.repo))
        nested=self.repo/'skills/example'
        nested.mkdir(parents=True)
        (nested/'.gitignore').write_text('!*.pyc\n')
        before={str(p):p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        errors, _=policy.hygiene(self.repo)
        self.assertTrue(any('skills/example/probe.pyc' in e for e in errors))
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.repo.rglob('*') if p.is_file()})

    def test_missing_rules_and_tracked_outputs_are_reported(self):
        (self.repo/'.gitignore').write_text('.DS_Store\n')
        self.assertTrue(policy.hygiene(self.repo)[0])
        (self.repo/'.gitignore').write_bytes((ROOT/'skills/_shared/templates/plugin/gitignore.txt').read_bytes())
        local=self.repo/'.tmp/evidence.txt'
        local.parent.mkdir();local.write_text('Fictional evidence to preserve')
        subprocess.run(['git','-C',str(self.repo),'add','-f','.tmp/evidence.txt'],check=True)
        errors,_=policy.hygiene(self.repo)
        self.assertTrue(any('already tracked' in e for e in errors))
        self.assertEqual('Fictional evidence to preserve',local.read_text())

    def test_missing_git_is_not_reported_as_success(self):
        with patch.object(policy,'git',side_effect=FileNotFoundError('git unavailable')):
            errors,warnings=policy.hygiene(self.repo)
        self.assertFalse(errors)
        self.assertTrue(any('incomplete' in w for w in warnings))

    def test_python_is_parsed_not_executed_and_missing_import_is_visible(self):
        files={'skills/example/scripts/main.py':b'import os\nimport helper\nraise RuntimeError("never execute")\n',
               'skills/example/scripts/helper.py':b'value = 1\n'}
        self.assertEqual(([],[]),policy.python_payload(files))
        del files['skills/example/scripts/helper.py']
        self.assertTrue(policy.python_payload(files)[1])
        files['skills/example/scripts/main.py']=b'def broken(\n'
        self.assertTrue(policy.python_payload(files)[0])

    def test_internal_builder_remains_available_for_current_plugin_create(self):
        self.assertTrue(callable(audit.scaffold_plugin))

    def test_extracted_packages_inspect_current_sources_and_reject_obsolete_init(self):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','PYTHONDONTWRITEBYTECODE')}
        source=self.root/'fictional-source';source.mkdir()
        (source/'SKILL.md').write_text('---\nname: fictional-example\ndescription: Fictional test.\n---\n# Example\n')
        for host in ('claude', 'codex'):
            with self.subTest(host=host):
                extracted=materialize(self.root/host, host)
                scripts=extracted/'skills/_shared/scripts'
                inspected=subprocess.run([sys.executable,str(scripts/'documentation.py'),'inspect','--source',str(source)],cwd=self.root,env=env,check=True,capture_output=True,text=True)
                self.assertEqual('fictional-example',json.loads(inspected.stdout)['name'])
                output=self.root/(host+'-initialized')
                result=subprocess.run([sys.executable,str(scripts/'plugin_audit.py'),'init'],cwd=self.root,env=env,check=False,capture_output=True,text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
                self.assertFalse(list(extracted.rglob('__pycache__')))
                self.assertFalse(list(output.rglob('__pycache__')))
