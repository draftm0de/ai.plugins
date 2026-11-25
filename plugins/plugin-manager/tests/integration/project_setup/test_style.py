"""R38: docs/style.md is created once by setup, required for docs only and never changed."""
import unittest

from tests.support.project_setup_fixture import Sandbox, tree


class StyleTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        self.assertEqual(0, self.box.call('setup')[0])
        (self.p / 'docs/style.md').unlink()

    def next_step(self):
        return self.box.call('status')[1]['next']

    def test_a_missing_style_is_the_open_step_and_closes_only_the_docs_gate(self):
        self.assertEqual('style', self.next_step())
        code, data, _ = self.box.call('gate', '--action', 'docs', '--message-language', 'de')
        self.assertEqual((1, False), (code, data['ready']))
        self.assertIn('der Schreibstil docs/style.md fehlt', data['message'])
        for action in ('modify', 'publish'):
            self.assertEqual(0, self.box.call('gate', '--action', action)[0], action)

    def test_the_template_is_copied_once_and_never_changed(self):
        code, data, _ = self.box.call('style', '--from-template')
        self.assertEqual((0, ['docs/style.md'], True), (code, data['created'], data['from_template']))
        self.assertIn('# Documentation style', (self.p / 'docs/style.md').read_text())
        self.assertEqual('ready', self.next_step())
        before = tree(self.p)
        code, data, _ = self.box.call('style', '--text', 'other')
        self.assertEqual((1, False), (code, data['ok']))
        self.assertIn('exists already', data['conflicts'][0]['reason'])
        self.assertEqual(before, tree(self.p))

    def test_the_text_of_the_person_is_saved_as_given(self):
        self.assertEqual(0, self.box.call('style', '--text', 'Duze die Leser. Kurze Sätze.')[0])
        self.assertEqual('Duze die Leser. Kurze Sätze.\n', (self.p / 'docs/style.md').read_text())
        self.assertEqual('ready', self.next_step())

    def test_an_empty_text_writes_nothing(self):
        before = tree(self.p)
        self.assertEqual(1, self.box.call('style', '--text', '  ')[0])
        self.assertEqual(before, tree(self.p))


if __name__ == '__main__':
    unittest.main()
