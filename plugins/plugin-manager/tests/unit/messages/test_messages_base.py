"""R30: the managed messages_base.py builds the layout once; the managed language helper raises coded failures."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SYNC = ROOT / 'skills/_shared/templates/plugin/sync/skills/_shared/scripts'
FORBIDDEN = re.compile(r'\b(exit|json|stderr|traceback|schema|evidence|hash|lock|manifest|migration|generator)\b|\b(Ihr|Ihre|Ihren|Ihrer|Ihnen)\b', re.I)


def load(name):
    spec = importlib.util.spec_from_file_location('managed_' + name, SYNC / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SYNC))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SYNC))
    return module


class MessagesBaseTests(unittest.TestCase):
    def setUp(self):
        self.base = load('messages_base')

    def test_every_base_entry_has_the_layout_in_both_languages_without_technical_words(self):
        for code in self.base.BASE_CATALOGUE:
            for language, headline, please, again in (('en', 'could not be completed, because', 'Please', 'Then call /demo:count again.'),
                                                      ('de', 'konnte nicht abgeschlossen werden, weil', 'Bitte', 'Rufe danach /demo:count erneut auf.')):
                text = self.base.render_failure(self.base.BASE_CATALOGUE, code, language, 'demo', 'count', path='/p')
                first, second = text.split('\n\n')
                self.assertIn(headline, first, code)
                self.assertTrue(second.startswith(please), code)
                self.assertTrue(second.endswith(again), code)
                self.assertNotIn('{', text, code)
                self.assertIsNone(FORBIDDEN.search(text), (code, language, text))

    def test_a_code_outside_the_catalogue_is_reported_as_not_known_and_extensions_use_the_same_layout(self):
        text = self.base.render_failure(self.base.BASE_CATALOGUE, 'NO_SUCH_CODE', 'de', 'demo', 'count')
        self.assertIn('weil die Ursache nicht bekannt ist', text)
        own = dict(self.base.BASE_CATALOGUE, OWN={'cause': {'en': 'x {path}', 'de': 'y {path}'}, 'fix': {'en': 'Please z', 'de': 'Bitte w'}})
        self.assertIn('because x /a.', self.base.render_failure(own, 'OWN', 'en', 'demo', 'count', path='/a'))
        self.assertEqual('en', self.base.pick_language('fr'))
        self.assertEqual('de', self.base.pick_language('de-AT'))

    def test_a_stop_says_was_stopped_and_a_named_change_replaces_nothing_was_changed(self):
        text = self.base.render_failure(self.base.BASE_CATALOGUE, 'UNKNOWN', 'en', 'demo', 'count', changed='The language you chose was saved.', stopped=True)
        self.assertTrue(text.startswith('The count action was stopped, because the cause is not known (an unexpected error). The language you chose was saved.'))

    def test_the_plugin_name_comes_from_plugin_json_never_from_a_constant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'skills/x/scripts').mkdir(parents=True)
            self.assertIsNone(self.base.plugin_name_from(root / 'skills/x/scripts/a.py'))
            (root / 'plugin.json').write_text(json.dumps({'name': 'word-counter'}))
            self.assertEqual('word-counter', self.base.plugin_name_from(root / 'skills/x/scripts/a.py'))
            (root / 'plugin.json').write_text(json.dumps({'name': 'renamed'}))
            self.assertEqual('renamed', self.base.plugin_name_from(root / 'skills/x/scripts/a.py'))

    def test_every_failure_code_of_the_language_helper_is_in_the_base_catalogue(self):
        codes = set(re.findall(r"OperatorLanguageError\('([A-Z_]+)'", (SYNC / 'operator_language.py').read_text()))
        self.assertTrue(codes)
        self.assertLessEqual(codes, set(self.base.BASE_CATALOGUE))

    def test_the_helper_prints_a_finished_message_in_the_requested_language_and_no_raw_text(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = str(Path(raw).resolve())  # the helper refuses a path that contains a link
            result = subprocess.run([sys.executable, '-B', '-I', str(SYNC / 'operator_language.py'), '--root', directory,
                                     '--set', 'not valid', '--skill', 'count', '--message-language', 'de'], capture_output=True, text=True)
            self.assertEqual((1, ''), (result.returncode, result.stdout))
            self.assertIn('Die Aktion count konnte nicht abgeschlossen werden, weil das Sprachkürzel nicht gültig ist.', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse((Path(directory) / '.project').exists())

    def test_the_command_frame_prints_finished_messages_and_never_raw_errors(self):
        import io
        base = self.base
        def configure(parser):
            parser.add_argument('--name', required=True)
        def body(args, language, out):
            if args.name == 'bad':
                raise base.Failure('LANGUAGE_TAG_INVALID')
            if args.name == 'boom':
                raise RuntimeError('raw internal text 17')
            out.write('ok ' + args.name + ' ' + language + '\\n')
        for argv, status, in_out, in_err in ((['--name', 'a', '--language', 'de'], 0, 'ok a de', ''),
                                             (['--name', 'bad', '--language', 'de'], 1, '', 'weil das Sprachkürzel nicht gültig ist'),
                                             (['--name', 'boom'], 1, '', 'because the cause is not known'),
                                             (['--language', 'de'], 1, '', 'weil der Aufruf unvollständig ist'),
                                             (['--unknown'], 1, '', 'because the call is incomplete')):
            out, err = io.StringIO(), io.StringIO()
            self.assertEqual(status, base.run('count', argv, 'demo', out, err, configure, body), argv)
            self.assertIn(in_out, out.getvalue())
            self.assertIn(in_err, err.getvalue())
            self.assertNotIn('raw internal text', err.getvalue())
            self.assertNotIn('Traceback', err.getvalue())

    def test_the_manager_ships_byte_identical_copies(self):
        for name in ('messages_base.py', 'operator_language.py'):
            self.assertEqual((SYNC / name).read_bytes(), (ROOT / 'skills/_shared/scripts' / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
