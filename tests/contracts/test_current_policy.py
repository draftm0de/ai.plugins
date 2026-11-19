from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]

class CurrentPolicyTests(unittest.TestCase):
    def test_obsolete_init_entrypoints_are_unavailable(self):
        shared = ROOT / 'plugins/plugin-manager/skills/_shared/scripts'
        for helper in ('workflows.py', 'plugin_audit.py'):
            result = subprocess.run([sys.executable, '-B', str(shared / helper), 'init'],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('invalid choice', result.stderr)
        self.assertFalse((ROOT / 'plugins/plugin-manager/commands/init.md').exists())
