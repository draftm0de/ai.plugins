"""Test collection must preserve opt-in boundaries and report failures."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class TestRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'scripts').mkdir()
        shutil.copy2(ROOT/'scripts/run_tests.py', self.root/'scripts/run_tests.py')
        (self.root/'tests').mkdir()
        (self.root/'tests/__init__.py').touch()

    def add(self, layer, text):
        directory = self.root/'tests'/layer
        directory.mkdir()
        (directory/'__init__.py').touch()
        (directory/'test_example.py').write_text(text)

    def run_tests(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.root/'scripts/run_tests.py'), *args],
                              cwd=self.root, capture_output=True, text=True)

    def test_native_layer_uses_only_current_gate(self):
        self.add('native', "import os, unittest\nclass Gates(unittest.TestCase):\n    def test_gate(self):\n        self.assertEqual(os.environ.get('AI_PLUGIN_TEST_NATIVE'), '1')\n        for key in ('PLUGIN_MANAGER_NATIVE','ZYRIS_TEST_SHARED_LOCAL','ZYRIS_TEST_LOCAL_NATIVE'):\n            self.assertNotIn(key, os.environ)\n")
        result = self.run_tests('--kind', 'native')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_never_imports_native_or_behavior(self):
        self.add('unit', 'import unittest\nclass Example(unittest.TestCase):\n    def test_ok(self): pass\n')
        for layer in ('native', 'behavior'):
            self.add(layer, "raise RuntimeError('must not import optional suite')\n")
        result = self.run_tests()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Ran 1 test', result.stderr)
        self.assertNotEqual(0, self.run_tests('--kind', 'native').returncode)

    def test_missing_layer_is_explicit_but_missing_group_fails(self):
        result = self.run_tests('--kind', 'native')
        self.assertEqual(0, result.returncode)
        self.assertIn('NOT RUN', result.stdout)
        self.assertNotEqual(0, self.run_tests('--group', 'unknown').returncode)

    def test_import_and_assertion_failures_propagate(self):
        self.add('contracts', "raise ImportError('fixture import failure')\n")
        self.assertNotEqual(0, self.run_tests().returncode)
        (self.root/'tests/contracts/test_example.py').write_text('import unittest\nclass Example(unittest.TestCase):\n    def test_failure(self): self.fail("fixture")\n')
        self.assertNotEqual(0, self.run_tests().returncode)

    def test_canonical_runner_copies_match(self):
        shared = ROOT/'plugins/plugin-manager/skills/_shared/templates'
        for path in (ROOT/'plugins/plugin-manager/scripts/run_tests.py',
                     shared/'plugin/scripts/run_tests.py', shared/'marketplace/scripts/run_tests.py'):
            self.assertEqual((ROOT/'scripts/run_tests.py').read_bytes(), path.read_bytes())
