"""The skill behavior cases are well-formed and their deterministic grading judges answers as intended."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
spec = importlib.util.spec_from_file_location('run_skills_under_test', ROOT / 'tests/behavior/run_skills.py')
run_skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_skills)
CASES = {case['id']: case for case in json.loads(run_skills.CASES.read_text())}


def answer(reply, commands=(), next_step='reports_only', writes=False):
    return {'reply': reply, 'commands': list(commands), 'next_step': next_step, 'writes': writes}


class CaseDefinitionTests(unittest.TestCase):
    def test_every_case_names_existing_skill_texts_and_valid_patterns(self):
        self.assertGreaterEqual(len(CASES), 7)
        for case in CASES.values():
            with self.subTest(case=case['id']):
                self.assertTrue((ROOT / 'skills' / case['skill'] / 'SKILL.md').is_file())
                for source in case['sources']:
                    self.assertTrue((ROOT / source.partition('#')[0]).is_file(), source)
                self.assertTrue(case['history'] and case['observed'])
                for key in ('required_commands', 'forbidden_commands'):
                    for pattern in case['expect'].get(key, []):
                        re.compile(pattern)
                self.assertIn(case['expect'].get('next_step', 'reports_only'), ('reports_only', 'asks_question', 'asks_confirmation'))

    def test_the_prompt_carries_the_real_skill_text_and_only_the_modify_excerpt_of_the_workflows(self):
        prompt = run_skills.build_prompt(CASES['modify_shows_consequences_and_asks_before_writing'])
        self.assertIn((ROOT / 'skills/modify/SKILL.md').read_text().strip().splitlines()[2], prompt)
        self.assertIn('--dry-run', prompt)
        self.assertNotIn('**publish**: read `references/publish.md`', prompt)  # an excerpt, not the whole file


class GradingTests(unittest.TestCase):
    def test_a_good_gate_stop_in_english_passes(self):
        case = CASES['docs_bare_gate_closed_language']
        good = answer('The documentation is not updated: the operator language is not saved yet. Please run /plugin-manager:setup first.')
        self.assertEqual([], run_skills.grade(case, good))

    def test_wrong_language_missing_pointer_questions_and_forbidden_commands_are_found(self):
        case = CASES['docs_bare_gate_closed_language']
        bad = answer('Die Dokumentation wird nicht erstellt. Soll ich das Setup starten?', ['python3 -B setup_state.py setup --target x'], 'asks_question', True)
        errors = ' | '.join(run_skills.grade(case, bad))
        for expected in ('not in en', 'does not mention /plugin-manager:setup', 'next_step', 'writes', 'question', 'forbidden command'):
            self.assertIn(expected, errors)

    def test_german_text_expects_a_german_stop(self):
        case = CASES['docs_german_text_gate_closed_sync']
        self.assertEqual([], run_skills.grade(case, answer('Die Dokumentation wird nicht aktualisiert: Eine Datei braucht noch eine Entscheidung. Bitte zuerst /plugin-manager:setup ausführen.')))
        self.assertIn('reply is not in de', run_skills.grade(case, answer('The documentation is not updated. Please run /plugin-manager:setup first.')))

    def test_modify_must_show_the_dry_run_and_ask_before_any_real_write(self):
        case = CASES['modify_shows_consequences_and_asks_before_writing']
        reply = 'The dry run would change plugin.json and the marketplace entry to "New description". Shall I write this? Yes or no?'
        self.assertEqual([], run_skills.grade(case, answer(reply, [], 'asks_confirmation')))
        writing = answer(reply, ['python3 -B "scripts/modify.py" --root x --description "New description"'], 'asks_confirmation')
        self.assertIn('forbidden command', ' '.join(run_skills.grade(case, writing)))

    def test_modify_writes_only_after_the_yes_with_the_agreed_values(self):
        case = CASES['modify_writes_only_after_the_yes']
        good = answer('The description is changed. Refresh the documentation with /plugin-manager:docs.',
                      ['python3 -B "scripts/modify.py" --root "/work/fictional-plugin" --description "New description"'], 'reports_only', True)
        self.assertEqual([], run_skills.grade(case, good))
        self.assertIn('missing command', ' '.join(run_skills.grade(case, answer('Done.', [], 'reports_only', True))))
        dry = answer('Checking.', ['python3 -B "scripts/modify.py" --root x --description "New description" --dry-run'], 'reports_only', True)
        self.assertIn('missing command', ' '.join(run_skills.grade(case, dry)))


if __name__ == '__main__':
    unittest.main()
