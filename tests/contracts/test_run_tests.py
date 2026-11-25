"""Layer selection of scripts/run_tests.py. Managed by plugin-manager; fictional data only."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PASSING = 'import unittest\nclass Example(unittest.TestCase):\n    def test_ok(self): pass\n'


class RunTestsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        shutil.copy2(ROOT / 'scripts/run_tests.py', self.root / 'scripts/run_tests.py')
        (self.root / 'tests').mkdir()
        (self.root / 'tests/__init__.py').touch()

    def add(self, layer, text):
        directory = self.root / 'tests' / layer
        directory.mkdir(exist_ok=True)
        (directory / '__init__.py').touch()
        (directory / 'test_example.py').write_text(text)

    def run_tests(self, *arguments):
        return subprocess.run([sys.executable, '-B', str(self.root / 'scripts/run_tests.py'), *arguments],
                              cwd=self.root, capture_output=True, text=True)

    def test_native_tests_run_only_with_their_gate(self):
        self.add('native', "import os, unittest\nclass Gate(unittest.TestCase):\n    def test_gate(self):\n"
                           "        self.assertEqual('1', os.environ.get('AI_PLUGIN_TEST_NATIVE'))\n")
        result = self.run_tests('--kind', 'native')
        self.assertEqual(0, result.returncode, result.stderr)

    def test_the_default_never_imports_native_or_behavior(self):
        self.add('unit', PASSING)
        for layer in ('native', 'behavior'):
            self.add(layer, "raise RuntimeError('optional suite must not be imported')\n")
        result = self.run_tests()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Ran 1 test', result.stderr)

    def test_a_missing_layer_is_reported_and_an_unknown_group_fails(self):
        result = self.run_tests('--kind', 'native')
        self.assertEqual(0, result.returncode)
        self.assertIn('NOT RUN', result.stdout)
        self.assertNotEqual(0, self.run_tests('--group', 'unknown').returncode)

    def test_import_and_assertion_failures_propagate(self):
        self.add('contracts', "raise ImportError('fictional import failure')\n")
        self.assertNotEqual(0, self.run_tests().returncode)
        self.add('contracts', PASSING.replace('pass', "self.fail('fictional')"))
        self.assertNotEqual(0, self.run_tests().returncode)


if __name__ == '__main__':
    unittest.main()
