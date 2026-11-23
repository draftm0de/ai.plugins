"""R26: every failure becomes its message in Python, in one layout, in both languages, from one catalogue."""
import re
import unittest
from pathlib import Path

from tests.support import project_setup_fixture as fx

ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN = re.compile(r'\b(exit|json|stderr|traceback|schema|evidence|hash|lock|manifest|migration|generator)\b|'
                       r'\b(Öffnen|Führen|Rufen|Prüfen|Starten|Wählen|Verwenden|Geben|Nutzen|Legen|Setzen) Sie\b|\b(Ihr|Ihre|Ihrem|Ihren|Ihrer|Ihnen)\b', re.I)
FACTS = {'path': '/Users/demo/plugin.a', 'root': '/Users/demo', 'address': 'https://x.test/a.git', 'origin': 'https://github.com/o/n.git'}


class MessagesTests(unittest.TestCase):
    def setUp(self):
        self.messages = fx.load_state().messages

    def test_every_catalogue_entry_has_the_layout_in_both_languages_and_no_technical_words(self):
        for code in self.messages.CATALOGUE:
            for lang, headline, please in (('en', 'could not be completed, because', 'Please'), ('de', 'konnte nicht abgeschlossen werden, weil', 'Bitte')):
                text = self.messages.render('setup', code, FACTS, lang, changed='language')
                first, second = text.split('\n\n')
                self.assertIn(headline, first, code)
                self.assertTrue(second.startswith(please), code)
                self.assertTrue(second.rstrip().endswith('/plugin-manager:setup again.' if lang == 'en' else '/plugin-manager:setup erneut auf.'), code)
                self.assertNotIn('{', text, code)  # every fact is filled
                self.assertIsNone(FORBIDDEN.search(text), (code, lang, text))
                self.assertNotRegex(text, r'^(Why|Warum|Solution|L[öo]sung)', code)

    def test_only_a_known_code_is_a_known_cause_everything_else_says_so_and_keeps_the_detail(self):
        known = self.messages.explain('docs', self.messages.Failure('no_origin', path='/x'), 'en')
        self.assertTrue(known['known'])
        self.assertIn('has no GitHub address yet', known['message'])
        for error in (RuntimeError('internal failure code 17'), ValueError('free text'), self.messages.Conflict if hasattr(self.messages, 'Conflict') else KeyError('k')):
            said = self.messages.explain('setup', error, 'de')
            self.assertFalse(said['known'])
            self.assertIn('weil die Ursache nicht bekannt ist', said['message'])
            self.assertNotIn('17', said['message'])
        self.assertIn('internal failure code 17', self.messages.explain('setup', RuntimeError('internal failure code 17'))['detail'])

    def test_a_state_conflict_with_a_known_code_uses_the_catalogue_with_the_folder(self):
        conflict = fx.load_state().Conflict('.', 'Folder has other content', 'not_fresh', ['a'])
        said = self.messages.explain('setup', conflict, 'de', folder='/Users/demo/p')
        self.assertTrue(said['known'])
        self.assertIn('Der Ordner /Users/demo/p bereits andere Dateien enthält'.replace('Der', 'der'), said['message'])

    def test_the_language_is_the_requested_one_else_the_saved_one_else_english(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual('en', self.messages.language_for(tmp))
            self.assertEqual('de', self.messages.language_for(tmp, 'de'))
            (Path(tmp) / '.project').mkdir()
            (Path(tmp) / '.project' / 'operator.json').write_text(json.dumps({'operator_language': 'de'}))
            self.assertEqual('de', self.messages.language_for(tmp))
            self.assertEqual('en', self.messages.language_for(tmp, 'en'))
            self.assertEqual('de', self.messages.language_for(tmp, 'fr'))  # a language outside the catalogue is ignored, the saved one counts

    def test_every_code_the_scripts_raise_is_in_the_catalogue_and_the_layout_exists_once(self):
        codes = set()
        for path in (ROOT / 'skills').rglob('*.py'):
            codes |= set(re.findall(r"failure\('([a-z_]+)'", path.read_text()))
            codes |= set(re.findall(r"Failure\('([a-z_]+)'", path.read_text()))
        self.assertTrue(codes)
        self.assertLessEqual(codes, set(self.messages.CATALOGUE))
        for path in (ROOT / 'skills').rglob('*.py'):  # no second place builds the layout
            if path.name not in ('messages.py', 'messages_base.py'):  # the Manager's catalogue module and the managed layout of the plugins
                self.assertNotIn('could not be completed, because', path.read_text(), path)
                self.assertNotIn('was stopped, because', path.read_text(), path)

    def test_the_gate_message_is_deterministic_in_both_languages(self):
        self.assertEqual('The docs action was stopped, because this folder is not set up yet, or only partly (a managed file needs your decision).\n\nPlease run /plugin-manager:setup first.',
                         self.messages.gate_message('docs', 'sync', 'en'))
        self.assertEqual('Die Aktion modify wurde abgebrochen, weil dieser Ordner noch nicht oder nur teilweise eingerichtet ist (eine verwaltete Datei braucht deine Entscheidung).\n\nFühre zuerst /plugin-manager:setup aus.',
                         self.messages.gate_message('modify', 'sync', 'de'))


if __name__ == '__main__':
    unittest.main()
