"""R23 state rule: the read-only `gate` answers whether a writing skill (docs, publish) may start."""
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
        self.assertEqual(before, tree(self.box.project))

    def test_gate_names_the_open_flow_for_every_state_before_ready(self):
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'skeleton'), (code, data['ready'], data['next']))

    def test_gate_is_open_when_configured_and_in_sync(self):
        self.setup_all()
        code, data, result = self.box.call('gate')
        self.assertEqual((0, True, 'ready'), (code, data['ready'], data['next']), result.stderr + result.stdout)

    def test_gate_stays_closed_while_a_sync_decision_is_open(self):
        self.setup_all()
        (self.p / 'alpha.md').write_bytes(b'# local change\n')
        self.box.set_template('alpha.md', b'# alpha v2\n')
        before = tree(self.p)
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'sync'), (code, data['ready'], data['next']))
        self.assertEqual(before, tree(self.p))

    def test_gate_reports_conflicts_as_closed(self):
        self.setup_all()
        (self.p / '.project/plugins/plugin-manager/config.json').write_text('{bad')
        code, data, _ = self.box.call('gate')
        self.assertEqual((1, False, 'stop'), (code, data['ready'], data['next']))


if __name__ == '__main__':
    unittest.main()
