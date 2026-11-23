"""Acceptance of the operator-language requirement for this plugin: the managed helper behaves as the requirement says.
Managed by the plugin manager, identical in every plugin; it runs the helper in temporary projects with fictional data."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / 'skills/_shared/scripts/operator_language.py'


def call(project, *args):
    return subprocess.run([sys.executable, '-B', '-I', str(HELPER), '--root', str(project), *args], capture_output=True, text=True)


class OperatorLanguageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()  # the helper refuses a path that contains a link

    def test_a_missing_preference_is_reported_without_writing(self):
        result = call(self.project)
        self.assertEqual((0, {'operator_language': None, 'needs_choice': True}), (result.returncode, json.loads(result.stdout)))
        self.assertEqual([], list(self.project.iterdir()))

    def test_an_explicit_choice_is_saved_per_project_and_reused(self):
        self.assertEqual({'operator_language': 'de', 'needs_choice': False}, json.loads(call(self.project, '--set', 'de').stdout))
        self.assertEqual('de', json.loads(call(self.project).stdout)['operator_language'])
        self.assertEqual({'schema_version': 1, 'operator_language': 'de'}, json.loads((self.project / '.project/operator.json').read_text()))
        other = self.project / 'other'
        other.mkdir()
        self.assertTrue(json.loads(call(other).stdout)['needs_choice'])  # another project is unaffected

    def test_an_invalid_tag_is_rejected_with_a_finished_message_and_nothing_is_written(self):
        result = call(self.project, '--set', 'not valid', '--skill', 'count', '--message-language', 'en')
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        self.assertIn('The count action', result.stderr)
        self.assertIn('because the language tag is not valid', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual([], list(self.project.iterdir()))

    def test_a_corrupt_or_unsupported_saved_setting_is_rejected_and_preserved(self):
        (self.project / '.project').mkdir()
        path = self.project / '.project/operator.json'
        for content in ('{broken', json.dumps({'schema_version': 2, 'operator_language': 'de'})):
            path.write_text(content)
            result = call(self.project, '--set', 'en')
            self.assertEqual(1, result.returncode)
            self.assertIn('has a format this version does not read', result.stderr)
            self.assertEqual(content, path.read_text())


if __name__ == '__main__':
    unittest.main()
