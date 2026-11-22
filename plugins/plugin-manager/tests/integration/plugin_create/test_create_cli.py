"""R22: the generator CLI has the uniform operations `create --kind marketplace|plugin` and `associate`."""
import json
import subprocess
import sys
import unittest

from tests.support.workflow_fixture import WorkflowFixture, flow


class UniformOperationTests(WorkflowFixture, unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(flow.SKILL / 'scripts/workflows.py'), *args],
                              capture_output=True, text=True, cwd=self.root)

    def snapshot(self):
        return {str(p): p.read_bytes() for base in (self.market, self.plugin) for p in base.rglob('*')
                if p.is_file() and '.git' not in p.parts}

    def test_former_subcommands_are_invalid_calls_without_alias(self):
        before = self.snapshot()
        for name in ('marketplace-create', 'plugin-create', 'configure'):
            with self.subTest(name=name):
                result = self.cli(name, '--root', str(self.plugin))
                self.assertEqual(2, result.returncode)
                self.assertIn('invalid choice', result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_create_needs_a_known_kind(self):
        for args in ((), ('--kind', 'website')):
            with self.subTest(args=args):
                self.assertEqual(2, self.cli('create', *args, '--root', str(self.plugin)).returncode)

    def test_arguments_of_the_other_kind_are_invalid_calls_before_any_write(self):
        before = self.snapshot()
        market = str(self.market)
        cases = {
            'marketplace + --marketplace': ('create', '--kind', 'marketplace', '--root', str(self.plugin), '--marketplace', market),
            'marketplace + --skeleton': ('create', '--kind', 'marketplace', '--root', str(self.plugin), '--skeleton'),
            'marketplace + --author': ('create', '--kind', 'marketplace', '--root', str(self.plugin), '--author', 'X'),
            'marketplace + --license': ('create', '--kind', 'marketplace', '--root', str(self.plugin), '--license', 'deferred'),
            'plugin + --owner': ('create', '--kind', 'plugin', '--root', str(self.plugin), '--marketplace', market, '--skeleton', '--owner', 'X'),
            'plugin without --marketplace': ('create', '--kind', 'plugin', '--root', str(self.plugin), '--skeleton'),
        }
        for label, args in cases.items():
            with self.subTest(label):
                result = self.cli(*args)
                self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_create_marketplace_reports_its_own_action(self):
        market = self.repo('second-market')
        result = self.cli('create', '--kind', 'marketplace', '--root', str(market), '--name', 'second-market',
                          '--display-name', 'Second Fictional Market', '--owner', 'Fictional Publisher')
        self.assertEqual(0, result.returncode, result.stderr)
        answer = json.loads(result.stdout)
        self.assertEqual(('create-marketplace', False), (answer['action'], answer['published']))
        self.assertTrue((market / 'marketplace.json').is_file())

    def test_create_plugin_reports_its_own_action(self):
        result = self.cli('create', '--kind', 'plugin', '--root', str(self.plugin), '--marketplace', str(self.market),
                          '--skeleton', '--name', 'new-plugin', '--display-name', 'Fictional Plugin', '--description', 'Fictional',
                          '--author', 'Fictional Publisher', '--languages', 'de', 'en', '--default-language', 'de', '--license', 'deferred')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('create-plugin', json.loads(result.stdout)['action'])
        self.assertTrue((self.plugin / 'plugin.json').is_file())

    def test_python_operations_follow_the_cli_names(self):
        for name in ('create_marketplace', 'create_plugin', 'associate'):
            self.assertTrue(callable(getattr(flow, name)), name)
        for name in ('marketplace_create', 'plugin_create', 'configure'):
            self.assertFalse(hasattr(flow, name), name)

    def test_help_lists_exactly_create_and_associate(self):
        result = self.cli('--help')
        self.assertEqual(0, result.returncode)
        self.assertIn('{create,associate}', result.stdout)


if __name__ == '__main__':
    unittest.main()
