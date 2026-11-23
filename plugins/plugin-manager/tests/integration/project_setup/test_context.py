"""R23: the real scripts run against mock data given as a context; the shipped command line stays closed."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import project_setup_fixture as fx
from tests.support.project_setup_fixture import FICTIONAL, FictionalSandbox, tree


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.box = FictionalSandbox().make(); self.addCleanup(self.box.close)

    def test_real_scripts_with_mock_parent_data_reach_ready_in_process(self):
        ps = fx.load_state(**self.box.ctx_args)
        self.assertEqual(self.box.source_root, ps.ctx.source_root)
        self.assertEqual(self.box.manager, ps.ctx.manager_root)
        self.assertEqual(fx.SHARED / 'scripts', ps.ctx.scripts_root)  # code is never mock data
        self.assertEqual({'plugin'}, set(ps.ctx.kinds))  # the mock parent knows exactly one kind
        self.assertEqual('language', ps.status(str(self.box.project))['next'])
        self.assertTrue(ps.language_only(str(self.box.project), 'de')['ok'])
        self.assertTrue(ps.setup(str(self.box.project))['ok'])
        self.assertEqual(sorted(FICTIONAL), sorted(self.box.lock()))
        self.assertEqual('ready', ps.status(str(self.box.project))['next'])
        self.assertEqual((True, 'ready'), tuple(ps.gate(str(self.box.project))[k] for k in ('ready', 'next')))

    def test_two_contexts_with_different_data_do_not_share_state(self):
        mock = fx.load_state(**self.box.ctx_args)
        real = fx.load_state()
        self.assertNotEqual(set(mock.ctx.kinds['plugin']['common']), set(real.ctx.kinds['plugin']['common']))
        self.assertEqual(set(FICTIONAL), set(mock.ctx.kinds['plugin']['common']))

    def test_context_rejects_an_invalid_plugin_and_unusable_parent_data(self):
        package = fx.load_state().package
        with self.assertRaises(package.Conflict):
            package.Context('Not A Name')
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(package.Conflict) as caught:
                package.Context(fx.PLUGIN, source_root=empty)
            self.assertEqual('template_base', caught.exception.code)

    def test_driver_runs_the_real_command_line_in_isolated_mode_with_mock_data(self):
        before = tree(self.box.manager)
        code, data, result = self.box.call('status')
        self.assertEqual((0, 'language'), (code, data['next']), result.stderr)
        self.assertEqual(before, tree(self.box.manager))  # no bytecode, no writes into the mock parent


class ShippedCommandLineTests(unittest.TestCase):
    """The shipped entry point takes no data root: it always uses the real parent."""

    def run_entry(self, *args):
        return subprocess.run([sys.executable, '-B', '-I', str(fx.HELPER), *args], capture_output=True, text=True, env={'PATH': ''})

    def test_status_and_gate_run_in_isolated_mode_from_the_real_entry_file(self):
        with tempfile.TemporaryDirectory() as folder:
            status = self.run_entry('status', '--target', folder, '--plugin', 'plugin-manager')
            gate = self.run_entry('gate', '--target', folder, '--plugin', 'plugin-manager')
        self.assertEqual((0, 'language'), (status.returncode, json.loads(status.stdout)['next']), status.stderr)
        self.assertEqual((1, False), (gate.returncode, json.loads(gate.stdout)['ready']), gate.stderr)

    def test_there_is_no_option_for_the_data_root(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_entry('status', '--target', folder, '--plugin', 'plugin-manager', '--source-root', folder)
        self.assertEqual(2, result.returncode)  # unknown option: argparse rejects it before any work


if __name__ == '__main__':
    unittest.main()
