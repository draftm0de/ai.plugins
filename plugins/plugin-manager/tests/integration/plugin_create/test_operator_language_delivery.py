"""Delivery of the operator-language building block; the helper itself is never executed."""
import json
import subprocess
import unittest

import workflows as flow
from tests.support.operator_language_fixture import GENERATOR, HELPER, MANAGER, REFERENCE
from tests.support.workflow_fixture import WorkflowFixture

RULE = '/.project/operator.json'


class CopyTests(unittest.TestCase):
    def test_manager_copies_are_byte_identical_to_canonical_generator_files(self):
        for relative in (HELPER, REFERENCE):
            self.assertEqual((GENERATOR / relative).read_bytes(), (MANAGER / relative).read_bytes(), relative)


class DeliveryTests(WorkflowFixture, unittest.TestCase):
    def lines(self, repository):
        return (repository / '.gitignore').read_text().splitlines()

    def test_created_plugin_ships_copies_and_exact_ignore_rule_without_preference(self):
        template = (flow.SKILL / 'templates/plugin/gitignore.txt').read_text().splitlines()
        self.create()
        for relative in (HELPER, REFERENCE):
            self.assertEqual((GENERATOR / relative).read_bytes(), (self.plugin / 'skills/_shared' / relative).read_bytes())
        lines = self.lines(self.plugin)
        self.assertEqual(1, lines.count(RULE))
        for rule in (r for r in template if r and not r.startswith('#')):
            self.assertIn(rule, lines)
        self.assertNotIn('.project/', lines)
        self.assertFalse((self.plugin / '.project').exists())
        self.assertEqual([], [str(p) for p in self.plugin.rglob('operator.json')])
        self.assertEqual([], [str(p) for p in self.plugin.rglob('__pycache__')])
        probe = subprocess.run(['git', '-C', str(self.plugin), 'check-ignore', '--no-index', '--', '.project/operator.json', '.project/other.json'],
                               capture_output=True, text=True)
        self.assertEqual(['.project/operator.json'], probe.stdout.split())

    def test_visible_text_language_rule_is_canonical_and_delivered_byte_identical(self):
        canonical = (GENERATOR / REFERENCE).read_text()
        for needle in ('## Language of all visible text', 'every visible text you write yourself uses it',
                       'closing summary or next-step card', 'button labels', 'Apply the language before output',
                       'Technical identifiers, paths, commands and JSON keys are not translated',
                       'Fixed labels the host itself supplies cannot be guaranteed', 'no card is forced'):
            self.assertIn(needle, canonical)
        self.assertEqual(canonical, (MANAGER / REFERENCE).read_text())
        self.create()
        delivered = (self.plugin / 'skills/_shared' / REFERENCE).read_bytes()
        self.assertEqual((GENERATOR / REFERENCE).read_bytes(), delivered)
        self.assertIn(b'## Language of all visible text', delivered)

    def test_existing_rule_and_project_rules_are_kept_without_duplicates(self):
        (self.plugin / '.gitignore').write_text('project-specific/\n' + RULE + '\n')
        self.create()
        lines = self.lines(self.plugin)
        self.assertEqual(1, lines.count(RULE)); self.assertIn('project-specific/', lines)

    def test_marketplace_ignore_behavior_is_unchanged(self):
        self.create()
        self.assertNotIn(RULE, self.lines(self.market))
        other = self.repo('second-market')
        flow.marketplace_create(other, 'second-market', 'Second', 'Fictional Publisher')
        self.assertNotIn(RULE, self.lines(other))
        self.assertFalse((other / 'skills/_shared/scripts/operator_language.py').exists())

    def test_configure_does_not_edit_ignore_rules_of_existing_plugin(self):
        self.create()
        text = '\n'.join(line for line in self.lines(self.plugin) if line != RULE) + '\n'
        (self.plugin / '.gitignore').write_text(text)
        flow.configure(self.plugin, self.market)
        self.assertEqual(text, (self.plugin / '.gitignore').read_text())
        self.assertNotIn(RULE, self.lines(self.market))

    def test_create_does_not_store_or_require_a_language(self):
        self.create()
        manifest = json.loads((self.plugin / 'plugin.json').read_text())
        self.assertNotIn('operator', json.dumps(manifest).lower())
        self.assertFalse((self.plugin / '.project').exists())


if __name__ == '__main__':
    unittest.main()
