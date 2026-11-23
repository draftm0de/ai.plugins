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


def answer(reply, commands=(), next_step='reports_only', writes=False, options=(), hands_over_to='none'):
    return {'reply': reply, 'commands': list(commands), 'next_step': next_step, 'writes': writes, 'options': list(options), 'hands_over_to': hands_over_to}


class CaseDefinitionTests(unittest.TestCase):
    def test_every_case_names_existing_skill_texts_and_valid_patterns(self):
        self.assertGreaterEqual(len(CASES), 10)
        for case in CASES.values():
            with self.subTest(case=case['id']):
                self.assertTrue((ROOT / 'skills' / case['skill'] / 'SKILL.md').is_file())
                for source in case['sources']:
                    self.assertTrue((ROOT / source.partition('#')[0]).is_file(), source)
                self.assertTrue(case['history'] and case['observed'])
                for key in ('required_commands', 'forbidden_commands'):
                    for pattern in case['expect'].get(key, []):
                        re.compile(pattern)
                wanted = case['expect'].get('next_step', 'reports_only')
                for label in (wanted if isinstance(wanted, list) else [wanted]):
                    self.assertIn(label, ('reports_only', 'asks_question', 'asks_confirmation'))

    def test_the_prompt_carries_the_real_skill_text_and_only_the_modify_excerpt_of_the_workflows(self):
        prompt = run_skills.build_prompt(CASES['modify_shows_consequences_and_asks_before_writing'])
        self.assertIn((ROOT / 'skills/modify/SKILL.md').read_text().strip().splitlines()[2], prompt)
        self.assertIn('--dry-run', prompt)
        self.assertNotIn('**publish**: read `references/publish.md`', prompt)  # an excerpt, not the whole file


class GradingTests(unittest.TestCase):
    def test_a_good_gate_stop_in_english_passes(self):
        case = CASES['docs_bare_gate_closed_language']
        good = answer('The docs action was stopped, because this folder is not set up yet, or only partly (the language is not set yet).\n\nPlease run /plugin-manager:setup first.\nRun /plugin-manager:setup now?',
                      next_step='asks_confirmation', options=['Yes, run it', 'No, stop'])
        self.assertEqual([], run_skills.grade(case, good))
        self.assertIn('options are', ' '.join(run_skills.grade(case, answer(good['reply'], next_step='asks_confirmation'))))  # no buttons offered
        unstructured = answer('The documentation is not updated: the language is not set yet. Please run /plugin-manager:setup first.', next_step='asks_confirmation', options=['Yes, run it', 'No, stop'])
        self.assertIn('in the required order', ' '.join(run_skills.grade(case, unstructured)))

    def test_wrong_language_missing_pointer_questions_and_forbidden_commands_are_found(self):
        case = CASES['docs_bare_gate_closed_language']
        bad = answer('Die Dokumentation wird nicht erstellt. Soll ich das Setup starten?\nUnd welchen Ordner meinst du?', ['python3 -B setup_state.py setup --target x'], 'reports_only', True)
        errors = ' | '.join(run_skills.grade(case, bad))
        for expected in ('not in en', 'required order', 'next_step', 'writes', 'question', 'forbidden command'):
            self.assertIn(expected, errors)

    def test_either_question_label_is_accepted_for_the_yes_no_question_and_a_bilingual_question_counts_once(self):
        case = CASES['docs_bare_gate_closed_language']
        reply = 'The docs action was stopped, because this folder is not set up yet, or only partly (x).\n\nPlease run /plugin-manager:setup first.'
        for label in ('asks_question', 'asks_confirmation'):
            self.assertEqual([], run_skills.grade(case, answer(reply, next_step=label, options=['Yes, run it', 'No, stop'])))
        self.assertIn('next_step', ' '.join(run_skills.grade(case, answer(reply, next_step='reports_only', options=['Yes, run it', 'No, stop']))))
        setup = CASES['setup_bare_asks_only_the_language_first']
        both = answer('Which language do you prefer? / Welche Sprache bevorzugst du?', next_step='asks_question')
        self.assertEqual([], run_skills.grade(setup, both))
        self.assertIn('question', ' '.join(run_skills.grade(setup, answer('Which language?\nAnd which folder?', next_step='asks_question'))))

    def test_german_text_expects_a_german_stop(self):
        case = CASES['docs_german_text_gate_closed_sync']
        self.assertEqual([], run_skills.grade(case, answer('Die Aktion docs wurde abgebrochen, weil dieser Ordner noch nicht oder nur teilweise eingerichtet ist (eine verwaltete Datei braucht deine Entscheidung).\n\nFühre zuerst /plugin-manager:setup aus.\nSoll ich /plugin-manager:setup jetzt ausführen?', next_step='asks_confirmation', options=['Ja, ausführen', 'Nein, abbrechen'])))
        self.assertIn('reply is not in de', ' '.join(run_skills.grade(case, answer('The docs action was stopped, because this folder is not set up yet. Please run /plugin-manager:setup first.'))))

    def test_a_yes_hands_over_to_setup_without_running_anything_and_a_no_ends(self):
        yes, no = CASES['docs_gate_closed_yes_hands_over_to_setup'], CASES['docs_gate_closed_no_ends_without_a_step']
        self.assertEqual([], run_skills.grade(yes, answer('Handing over to /plugin-manager:setup.', hands_over_to='setup')))
        self.assertIn('hands_over_to', ' '.join(run_skills.grade(yes, answer('Handing over.'))))
        self.assertIn('forbidden command', ' '.join(run_skills.grade(yes, answer('Running setup.', ['python3 -B setup_state.py setup --target x'], hands_over_to='setup'))))
        self.assertEqual([], run_skills.grade(no, answer('Understood, I stop here.')))
        self.assertIn('hands_over_to', ' '.join(run_skills.grade(no, answer('Starting setup.', hands_over_to='setup'))))

    def test_a_failure_must_be_told_in_plain_words_with_the_command(self):
        case = CASES['setup_failure_is_explained_in_plain_words']
        good = answer('Das Setup konnte nicht abgeschlossen werden, weil der Ordner /Users/demo/tests/demo.plugin.a nicht als Git-Repository erkannt wird. Die Sprache wurde gespeichert.\n\nBitte initialisiere es entweder in einer IDE (zum Beispiel VS Code) oder führe in einem Terminal in diesem Ordner `git init` aus. Rufe danach /plugin-manager:setup erneut auf.')
        self.assertEqual([], run_skills.grade(case, good))
        technical = answer('Der Generator lief mit Exit 1 und checks.status != passed. Der Ordner ist kein Git-Repository: `git init`. Das JSON zeigt conflicts.')
        errors = ' '.join(run_skills.grade(case, technical))
        self.assertIn('technical wording', errors)
        self.assertIn('reply is not in de', ' '.join(run_skills.grade(case, answer('The folder is not a Git repository. Run `git init` in it.'))))

    def test_missing_git_must_use_the_catalogue_wording_not_a_free_one(self):
        case = CASES['setup_missing_git_uses_the_catalogue_message_before_other_questions']
        good = answer('Das Setup konnte nicht abgeschlossen werden, weil der Ordner /Users/demo/tests/demo.plugin.a nicht als Git-Repository erkannt wird. Die Sprache wurde gespeichert.\n\nBitte initialisiere es entweder in einer IDE (zum Beispiel VS Code) oder führe in einem Terminal in diesem Ordner `git init` aus. Rufe danach /plugin-manager:setup erneut auf.')
        self.assertEqual([], run_skills.grade(case, good))
        free = answer('Die Konfiguration kann noch nicht weitergehen, weil der Ordner kein Git-Checkout ist und es keinen GitHub-origin gibt. Bitte initialisiere ein Repository und rufe /plugin-manager:setup erneut auf.')
        errors = ' '.join(run_skills.grade(case, free))
        self.assertIn('technical wording', errors)
        self.assertIn('git init', errors)

    def test_a_german_message_uses_du_not_sie(self):
        case = CASES['setup_failure_is_explained_in_plain_words']
        formal = answer('Das Setup konnte nicht abgeschlossen werden, weil der Ordner kein Git-Repository ist.\n\nFühren Sie `git init` aus und rufen Sie /plugin-manager:setup erneut auf.')
        self.assertIn('technical wording', ' '.join(run_skills.grade(case, formal)))
        informal = answer('Das Setup konnte nicht abgeschlossen werden, weil der Ordner kein Git-Repository ist.\n\nFühre `git init` aus und rufe danach /plugin-manager:setup erneut auf.')
        self.assertNotIn('technical wording', ' '.join(run_skills.grade(case, informal)))

    def test_an_unknown_failure_is_not_guessed_and_offers_the_details(self):
        case = CASES['setup_unknown_failure_is_not_guessed']
        good = answer('Das Setup konnte nicht abgeschlossen werden, weil die Ursache nicht bekannt ist (ein unerwarteter Fehler). Es wurde nichts geändert.\n\nBitte rufe entweder /plugin-manager:setup erneut auf oder prüfe den Ordner mit /plugin-manager:verify.\nMöchtest du die technischen Details sehen?',
                      next_step='asks_question', options=['Technische Details anzeigen', 'Nein, danke'])
        self.assertEqual([], run_skills.grade(case, good))
        guessed = answer('Das Setup konnte nicht abgeschlossen werden, weil der Fehlercode 17 bedeutet, dass der Speicher voll ist.\n\nRäume auf.', next_step='reports_only')
        errors = ' '.join(run_skills.grade(case, guessed))
        self.assertIn('technical wording', errors)
        self.assertIn('mentions none of', errors)

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
