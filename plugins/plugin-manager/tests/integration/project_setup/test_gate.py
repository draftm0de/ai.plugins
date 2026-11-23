"""R23 state rule: the read-only `gate` answers whether a writing skill (docs, publish) may start."""
import re
import unittest

from tests.integration.project_setup.test_sync import SyncBase
from tests.support.project_setup_fixture import tree


class GateTests(SyncBase):
    def test_gate_is_closed_before_the_workpackage_is_ready_and_writes_nothing(self):
        self.box.unconfigure()
        before = tree(self.box.project)
        code, data, result = self.box.call('gate')
        self.assertEqual(1, code, result.stderr + result.stdout)
        self.assertEqual((False, 'language'), (data['ready'], data['next']))
        self.assertTrue(data['reason'])
        self.assertEqual('The requested action was stopped.\nWhy:\nThis folder is not set up yet, or only partly (the language is not set yet).\nSolution:\nRun /plugin-manager:setup first.', data['message'])
        self.assertEqual(before, tree(self.box.project))

    def test_gate_names_the_open_flow_for_every_state_before_ready(self):
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'skeleton'), (code, data['ready'], data['next']))

    def test_gate_is_open_when_configured_and_in_sync(self):
        self.setup_all()
        code, data, result = self.box.call('gate')
        self.assertEqual((0, True, 'ready'), (code, data['ready'], data['next']), result.stderr + result.stdout)
        self.assertIsNone(data['message'])  # nothing to report when the gate is open

    def test_gate_stays_closed_while_a_sync_decision_is_open(self):
        self.setup_all()
        (self.p / 'alpha.md').write_bytes(b'# local change\n')
        self.box.set_template('alpha.md', b'# alpha v2\n')
        before = tree(self.p)
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'sync'), (code, data['ready'], data['next']))
        self.assertEqual(before, tree(self.p))

    def test_the_message_names_the_gated_skill_and_has_the_same_structure_for_every_cause(self):
        shapes = set()
        for action in ('docs', 'modify', 'publish'):
            code, data, _ = self.box.call('gate', '--action', action)
            self.assertEqual(1, code)
            self.assertTrue(data['message'].startswith('The ' + action + ' action was stopped.\nWhy:\n'))
            shapes.add(re.sub(r'\(.*?\)', '(...)', data['message']).replace(action, '<action>'))
        self.assertEqual(1, len(shapes))
        self.assertIn('\nSolution:\nRun /plugin-manager:setup first.', data['message'])
        self.assertEqual(2, self.box.call('gate', '--action', 'verify')[0])  # only gated skills are known

    def test_gate_reports_conflicts_as_closed(self):
        self.setup_all()
        (self.p / '.project/plugins/plugin-manager/config.json').write_text('{bad')
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'stop'), (code, data['ready'], data['next']))
        self.assertIn('Why:\nThis folder is not set up yet, or only partly (something in this folder blocks the setup)', data['message'])
        self.assertIn('configuration evidence', data['detail'])  # the technical detail is kept, but stays out of the message
        self.assertNotIn('evidence', data['message'])


if __name__ == '__main__':
    unittest.main()
