"""R26: the check before a configuration returns the finished message, in the language of the person."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / 'skills/_shared/scripts/workflows.py'


def run(*args):
    return subprocess.run([sys.executable, '-B', str(HELPER), 'prerequisites', *args], text=True, capture_output=True)


class PrerequisitesTests(unittest.TestCase):
    def test_a_plugin_folder_without_git_gets_both_steps_in_german(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run('--kind', 'plugin', '--root', tmp, '--message-language', 'de', '--changed', 'language')
            self.assertEqual(1, result.returncode)
            first, second = result.stderr.split('\n\n', 1)
            self.assertIn('Die Aktion setup konnte nicht abgeschlossen werden, weil der Ordner', first)
            self.assertIn('Die Sprache, die du gewählt hast, wurde gespeichert.', first)
            self.assertIn('`git init`', second)
            self.assertIn('`git remote add origin https://github.com/<owner>/<name>.git`', second)
            self.assertIn('Rufe danach /plugin-manager:setup erneut auf.', second)

    def test_a_marketplace_without_git_needs_only_git_init_and_a_repository_without_origin_only_the_address(self):
        with tempfile.TemporaryDirectory() as tmp:
            market = run('--kind', 'marketplace', '--root', tmp, '--message-language', 'en')
            self.assertIn('`git init`', market.stderr)
            self.assertNotIn('remote add origin', market.stderr)
            subprocess.run(['git', 'init', '-q', tmp], check=True)
            plugin = run('--kind', 'plugin', '--root', tmp, '--message-language', 'en')
            self.assertIn('has no GitHub address yet', plugin.stderr)
            self.assertNotIn('git init', plugin.stderr.split('[Technical')[0])
            self.assertEqual(0, run('--kind', 'marketplace', '--root', tmp).returncode)
            subprocess.run(['git', '-C', tmp, 'remote', 'add', 'origin', 'https://github.com/o/n.git'], check=True)
            self.assertEqual(0, run('--kind', 'plugin', '--root', tmp).returncode)


if __name__ == '__main__':
    unittest.main()
