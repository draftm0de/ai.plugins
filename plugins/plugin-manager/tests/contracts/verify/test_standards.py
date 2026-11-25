"""R27: the standards come with every plugin, identical, and verify finds a missing, changed or copied standard."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

R = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(R / 'skills/_shared/scripts'))
import plugin_audit as audit
import verify as skill_verify

NAMES = ('coding.md', 'messages.md', 'testing.md', 'skills.md')
SOURCE = R / 'skills/_shared/templates/plugin/sync/docs/standards'


class StandardsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name).resolve()
        source = root / 'source'
        source.mkdir()
        (source / 'SKILL.md').write_text('---\nname: fictional-example\ndescription: A fictional test capability.\n---\n# Example\n')
        self.plugin = root / 'plugin'
        audit.scaffold_plugin(source, self.plugin, languages=['de', 'en'], repository='https://github.com/example/fictional', author='Fictional Team')

    def status(self):
        return {c['id']: c['status'] for c in audit.audit(self.plugin)['checks'] if c['id'].startswith('standards:')}

    def test_a_new_plugin_has_the_four_standards_identical_to_the_managed_ones(self):
        for name in NAMES:
            self.assertEqual((SOURCE / name).read_bytes(), (self.plugin / 'docs/standards' / name).read_bytes(), name)
        self.assertEqual({'standards:' + n: 'pass' for n in NAMES} | {'standards:AGENTS.md': 'pass', 'standards:scope': 'pass'}, self.status())
        agents = (self.plugin / 'AGENTS.md').read_text()
        for name in NAMES:
            self.assertIn('\n@docs/standards/' + name, agents)
        self.assertIn('\n@CUSTOM.AGENTS.md', agents)
        self.assertEqual('@AGENTS.md', (self.plugin / 'CLAUDE.md').read_text().split('-->')[1].strip())

    def test_a_missing_or_changed_standard_is_a_finding(self):
        (self.plugin / 'docs/standards/coding.md').write_text('my own rules\n')
        (self.plugin / 'docs/standards/testing.md').unlink()
        found = self.status()
        self.assertEqual(('fail', 'fail'), (found['standards:coding.md'], found['standards:testing.md']))
        self.assertEqual('pass', found['standards:messages.md'])
        self.assertFalse(audit.audit(self.plugin)['structurally_valid'])

    def test_agents_md_is_the_managed_one_and_plugin_specific_text_belongs_into_custom_agents_md(self):  # R28
        agents = self.plugin / 'AGENTS.md'
        agents.write_text(agents.read_text() + '\nMy own rule.\n')
        self.assertEqual('fail', self.status()['standards:AGENTS.md'])
        self.assertTrue((self.plugin / 'CUSTOM.AGENTS.md').is_file())

    def test_a_standard_copied_into_the_scope_is_a_finding(self):
        line = next(l.strip() for l in (SOURCE / 'coding.md').read_text().splitlines() if len(l.strip()) >= 60)
        scope = self.plugin / 'SCOPE.md'
        scope.write_text(scope.read_text() + '\n' + line + '\n')
        self.assertEqual('fail', self.status()['standards:scope'])

    def test_the_verify_skill_reports_a_missing_changed_or_unreferenced_standard_and_a_copy_in_scope(self):  # R27
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])
        standard = self.plugin / 'docs/standards/coding.md'
        original = standard.read_bytes()
        standard.write_text('my own rules\n')
        self.assertIn('differs from the managed standard', ' '.join(skill_verify.verify(self.plugin, 'plugin')['errors']))
        standard.unlink()
        self.assertIn('docs/standards/coding.md is missing', ' '.join(skill_verify.verify(self.plugin, 'plugin')['errors']))
        standard.write_bytes(original)
        agents = self.plugin / 'AGENTS.md'
        text = agents.read_text()
        agents.write_text(text.split('## Standards')[0])
        self.assertIn('AGENTS.md differs from the managed one', ' '.join(skill_verify.verify(self.plugin, 'plugin')['errors']))
        agents.write_text(text)
        line = next(l.strip() for l in original.decode().splitlines() if len(l.strip()) >= 60)
        scope = self.plugin / 'SCOPE.md'
        scope.write_text(scope.read_text() + '\n' + line + '\n')
        self.assertIn('SCOPE.md copies standard text', ' '.join(skill_verify.verify(self.plugin, 'plugin')['errors']))

    def test_the_manager_follows_its_own_standards_and_all_copies_of_the_verifier_agree(self):
        for name in NAMES:
            self.assertEqual((SOURCE / name).read_bytes(), (R / 'docs/standards' / name).read_bytes(), name)
        self.assertTrue(skill_verify.verify(R, 'plugin')['structure_valid'])
        canonical = (R / 'skills/_shared/scripts/verify.py').read_bytes()
        for relative in ('scripts/verify.py', 'skills/_shared/templates/plugin/sync/scripts/verify.py', 'skills/_shared/templates/marketplace/sync/scripts/verify.py'):
            self.assertEqual(canonical, (R / relative).read_bytes(), relative)

    def errors(self):
        return ' '.join(skill_verify.verify(self.plugin, 'plugin').get('errors', []))

    def test_a_plugin_with_exactly_one_skill_needs_no_command_file_and_with_several_each_skill_needs_one(self):  # R32
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])
        second = self.plugin / 'skills/second'
        second.mkdir()
        (second / 'SKILL.md').write_text('---\nname: second\ndescription: A fictional second capability.\n---\n# Second\n')
        self.assertIn('has no commands/', self.errors())
        (self.plugin / 'commands').mkdir(exist_ok=True)
        for name in ('fictional-example', 'second'):
            (self.plugin / 'commands' / (name + '.md')).write_text('Run the skill.\n')
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])

    def test_the_failure_layout_exists_only_in_the_message_module(self):  # R32
        script = self.plugin / 'skills/fictional-example/scripts/run.py'
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("MESSAGE = 'The count action could not be completed, because x'\n")
        self.assertIn('builds a failure message itself', self.errors())
        script.write_text("MESSAGE = 'a plain text'\n")
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])

    def test_every_failure_code_used_in_the_scripts_needs_a_catalogue_entry(self):  # R32
        scripts = self.plugin / 'skills/_shared/scripts'
        (scripts / 'work.py').write_text("from messages_base import Failure\nraise Failure('NO_ENTRY_FOR_THIS')\n")
        self.assertIn('failure codes without a catalogue entry: NO_ENTRY_FOR_THIS', self.errors())
        (scripts / 'catalogue.py').write_text("CATALOGUE = {'NO_ENTRY_FOR_THIS': {}}\n")
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])

    def test_test_folders_follow_the_standard(self):  # R32
        (self.plugin / 'tests/regression').mkdir()
        self.assertIn('tests/regression is not a test folder', self.errors())
        (self.plugin / 'tests/regression').rmdir()
        nested = self.plugin / 'tests/unit/thing'
        nested.mkdir(parents=True)
        (nested / 'test_x.py').write_text('')
        self.assertIn('has test files but no __init__.py', self.errors())
        (self.plugin / 'tests/unit/__init__.py').write_text('')
        (nested / '__init__.py').write_text('')
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])

    def run_copy(self, *command):
        return subprocess.run(list(command), cwd=self.plugin, capture_output=True, text=True)

    def lock_standards(self):
        files = {}
        for relative in ['docs/standards/' + name for name in NAMES] + ['AGENTS.md']:
            digest = hashlib.sha256((self.plugin / relative).read_bytes()).hexdigest()
            files[relative] = {'source_hash': digest, 'local_hash': digest}
        lock = self.plugin / '.project/plugins/plugin-manager/skeleton.json'
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps({'schema_version': 2, 'files': files}))

    def test_the_plugin_copy_of_the_verifier_finds_a_changed_standard_through_the_committed_lock(self):  # R33
        self.lock_standards()
        command = (sys.executable, '-B', 'scripts/verify.py', '--source', '.', '--kind', 'plugin')
        self.assertEqual(0, self.run_copy(*command).returncode, self.run_copy(*command).stdout)
        standard = self.plugin / 'docs/standards/testing.md'
        standard.write_text(standard.read_text() + 'my own rule\n')
        result = self.run_copy(*command)
        self.assertEqual(1, result.returncode)
        self.assertIn('docs/standards/testing.md differs from the managed standard', result.stdout)

    def test_the_ci_of_a_new_plugin_runs_the_verifier(self):  # R33
        workflow = (self.plugin / '.github/workflows/validate.yml').read_text()
        self.assertIn('run: python3 -B scripts/verify.py --source . --kind plugin', workflow)

    def test_the_managed_pre_commit_hook_is_silent_when_valid_and_stops_with_the_findings_when_not(self):  # R33
        hook = self.plugin / 'githooks/pre-commit'
        self.assertTrue(os.access(hook, os.X_OK))
        good = self.run_copy('sh', 'githooks/pre-commit')
        self.assertEqual((0, '', ''), (good.returncode, good.stdout, good.stderr))
        (self.plugin / 'docs/standards/coding.md').unlink()
        bad = self.run_copy('sh', 'githooks/pre-commit')
        self.assertEqual(1, bad.returncode)
        self.assertIn('docs/standards/coding.md is missing', bad.stderr)

    def test_nothing_activates_the_hook_without_the_person(self):  # R33
        self.assertIn('git config core.hooksPath githooks', (self.plugin / 'Makefile').read_text())
        for path in (R / 'skills').rglob('*.py'):
            self.assertNotIn('core.hooksPath githooks', path.read_text(), path)

    def test_the_manager_documentation_uses_the_managed_concepts_pages(self):  # R36
        for language in ('de', 'en'):
            self.assertEqual((R / 'skills/_shared/templates/plugin/sync/docs' / language / 'concepts.md').read_bytes(),
                             (R / 'docs' / language / 'concepts.md').read_bytes(), language)

    def test_a_plugin_without_its_documentation_style_is_a_finding_and_the_runtime_style_is_optional(self):  # R38
        self.assertTrue((self.plugin / 'docs/style.md').is_file())
        self.assertFalse((self.plugin / 'skills/_shared/references/style.md').exists())
        self.assertTrue(skill_verify.verify(self.plugin, 'plugin')['structure_valid'])
        (self.plugin / 'docs/style.md').unlink()
        self.assertIn('docs/style.md is missing', self.errors())


if __name__ == '__main__':
    unittest.main()
