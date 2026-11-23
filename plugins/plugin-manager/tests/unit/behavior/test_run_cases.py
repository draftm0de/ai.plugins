"""R31: the managed model-case runner of every plugin grades deterministically and never needs a model for its own tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / 'skills/_shared/templates/plugin/sync/tests/behavior/run_cases.py'
spec = importlib.util.spec_from_file_location('managed_run_cases', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def answer(reply, commands=(), next_step='reports_only', options=(), writes=False):
    return {'reply': reply, 'commands': list(commands), 'next_step': next_step, 'options': list(options), 'writes': writes}


CASE = {'id': 'x', 'sources': ['skills/a/SKILL.md'], 'history': [{'role': 'person', 'text': '/p:a'}],
        'observed': [{'command': 'run a', 'output': 'message text'}],
        'expect': {'language': 'en', 'contains': ['message text'], 'in_order': ['message', 'text'], 'writes': False, 'max_questions': 0,
                   'forbidden_text': [r'\bexit\b'], 'forbidden_commands': [r'--confirm'], 'next_step': 'reports_only'}}


class GradingTests(unittest.TestCase):
    def test_a_good_answer_passes_and_every_rule_is_found_when_broken(self):
        self.assertEqual([], runner.grade(CASE, answer('This is the message text, not changed.')))
        errors = ' | '.join(runner.grade(CASE, answer('Der Exit war nicht gut? Wirklich? exit', ['run --confirm'], 'asks_question', writes=True)))
        for expected in ('not in en', 'does not contain', 'technical wording', 'forbidden command', 'next_step', 'writes', 'question'):
            self.assertIn(expected, errors)
        self.assertEqual(['empty reply'], runner.grade(CASE, answer('  ')))

    def test_optional_rules(self):
        case = {'expect': {'mentions_any': ['alpha', 'beta'], 'options': ['Yes', 'No'], 'required_commands': [r'^run ']}}
        self.assertEqual([], runner.grade(case, answer('beta', ['run it'], options=['Yes', 'No'])))
        errors = ' | '.join(runner.grade(case, answer('gamma')))
        for expected in ('mentions none of', 'options are', 'missing command'):
            self.assertIn(expected, errors)

    def test_the_prompt_holds_the_real_skill_text_the_observed_output_and_the_conversation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'skills/a').mkdir(parents=True)
            (root / 'skills/a/SKILL.md').write_text('SKILL BODY')
            prompt = runner.build_prompt(CASE, root)
        for part in ('SKILL BODY', '$ run a\nmessage text', 'PERSON: /p:a', 'no tools'.replace('no tools', 'All tools are unavailable')):
            self.assertIn(part, prompt)

    def test_the_command_line_runs_without_cases_and_lists_cases_without_a_model(self):
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory)
            (plugin / 'tests/behavior').mkdir(parents=True)
            copy = plugin / 'tests/behavior/run_cases.py'
            copy.write_bytes(RUNNER.read_bytes())
            result = subprocess.run([sys.executable, '-B', str(copy), '--list'], capture_output=True, text=True)
            self.assertEqual((0, True), (result.returncode, 'NOT RUN' in result.stdout))
            (plugin / 'tests/fixtures/skills').mkdir(parents=True)
            (plugin / 'tests/fixtures/skills/cases.json').write_text(json.dumps([CASE]))
            result = subprocess.run([sys.executable, '-B', str(copy), '--list'], capture_output=True, text=True)
            self.assertEqual(('x', 0), (result.stdout.strip(), result.returncode))
            self.assertEqual(2, subprocess.run([sys.executable, '-B', str(copy)], capture_output=True, text=True).returncode)  # --cli required


if __name__ == '__main__':
    unittest.main()
