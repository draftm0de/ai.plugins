"""CLI behavior of the operator-language helper from an isolated plugin copy."""
import ast
import json
import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path

from tests.support.operator_language_fixture import GENERATOR, HELPER, Sandbox, run, tree


def run_without_root(helper, *args, cwd=None):
    return subprocess.run([sys.executable, '-B', '-I', str(helper), *args],
                          capture_output=True, text=True, cwd=cwd, env={'PATH': ''})


MISSING = {'operator_language': None, 'needs_choice': True}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(); self.addCleanup(self.box.close)
        self.project, self.helper = self.box.project, self.box.helper

    def call(self, *args, root=None):
        return run(self.helper, root or self.project, *args, cwd=self.box.base)

    def stored(self, root=None):
        return (root or self.project) / '.project/operator.json'

    def test_read_in_empty_project_creates_nothing_and_reports_missing(self):
        plugin_before = tree(self.helper.parents[2])
        result = self.call()
        self.assertEqual((0, MISSING), (result.returncode, json.loads(result.stdout)))
        self.assertEqual({}, tree(self.project))
        self.assertEqual(plugin_before, tree(self.helper.parents[2]))  # no bytecode, plugin unchanged

    def test_save_read_same_value_and_targeted_change(self):
        result = self.call('--set', 'de')
        self.assertEqual((0, {'operator_language': 'de', 'needs_choice': False}), (result.returncode, json.loads(result.stdout)))
        self.assertEqual({'schema_version': 1, 'operator_language': 'de'}, json.loads(self.stored().read_text()))
        self.assertEqual('de', json.loads(self.call().stdout)['operator_language'])
        inode, content = self.stored().stat().st_ino, self.stored().read_bytes()
        self.assertEqual(0, self.call('--set', 'de').returncode)
        self.assertEqual((inode, content), (self.stored().stat().st_ino, self.stored().read_bytes()))  # unchanged, not rewritten
        self.assertEqual(0, self.call('--set', 'pt-BR').returncode)
        self.assertEqual('pt-BR', json.loads(self.call().stdout)['operator_language'])
        self.assertEqual({'.project', '.project/operator.json'}, set(tree(self.project)))  # no temp files left

    def test_invalid_input_and_existing_corrupt_state_stay_unchanged(self):
        self.assertEqual(1, self.call('--set', 'Deutsch!').returncode)
        self.assertEqual({}, tree(self.project))
        self.stored().parent.mkdir()
        for content in ('{', '{"schema_version": 2, "operator_language": "de"}', '{"schema_version": 1, "operator_language": ""}'):
            self.stored().write_text(content)
            before = tree(self.project)
            for args in ((), ('--set', 'en'), ('--set', '!')):
                result = self.call(*args)
                self.assertEqual(1, result.returncode, (content, args))
                self.assertEqual('', result.stdout)
                self.assertTrue(result.stderr.strip())
                self.assertNotEqual(MISSING, result.stdout)
            self.assertEqual(before, tree(self.project))

    def test_projects_are_independent(self):
        other = self.box.base / 'other'; other.mkdir()
        self.assertEqual(0, self.call('--set', 'de').returncode)
        self.assertEqual(MISSING, json.loads(self.call(root=other).stdout))
        self.assertEqual(0, self.call('--set', 'en', root=other).returncode)
        self.assertEqual('de', json.loads(self.call().stdout)['operator_language'])
        self.assertEqual('en', json.loads(self.call(root=other).stdout)['operator_language'])

    def test_symlinks_and_conflicts_are_rejected_without_writes(self):
        target = self.box.base / 'foreign'; target.mkdir()
        (self.project / '.project').symlink_to(target, target_is_directory=True)
        for args in ((), ('--set', 'de')):
            self.assertEqual(1, self.call(*args).returncode)
        self.assertEqual({}, tree(target))
        (self.project / '.project').unlink(); (self.project / '.project').mkdir()
        (target / 'file.json').write_text('{"schema_version": 1, "operator_language": "fr"}')
        self.stored().symlink_to(target / 'file.json')
        for args in ((), ('--set', 'de')):
            self.assertEqual(1, self.call(*args).returncode)
        self.assertEqual('{"schema_version": 1, "operator_language": "fr"}', (target / 'file.json').read_text())
        link = self.box.base / 'linked project'; link.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(1, self.call('--set', 'de', root=link).returncode)

    def test_invalid_cli_arguments_exit_2_and_leave_project_unchanged(self):
        self.assertEqual(0, self.call('--set', 'de').returncode)
        before = tree(self.project)
        invalid = (('--unknown',), ('--set',), ('--set', 'en', 'extra'), ('--set', 'en', '--bogus'))
        for args in invalid:
            result = self.call(*args)
            self.assertEqual(2, result.returncode, args)
            self.assertEqual('', result.stdout)
            self.assertIn('usage:', result.stderr)
            self.assertEqual(before, tree(self.project))
        for args in ((), ('--set', 'en')):  # --root missing
            result = run_without_root(self.helper, *args, cwd=self.box.base)
            self.assertEqual((2, ''), (result.returncode, result.stdout))
            self.assertIn('--root', result.stderr)
            self.assertEqual(before, tree(self.project))
        fresh = self.box.base / 'untouched'; fresh.mkdir()
        self.assertEqual(2, self.call('--unknown', root=fresh).returncode)
        self.assertEqual({}, tree(fresh))

    def test_regular_file_as_project_directory_is_a_path_conflict_on_read(self):
        (self.project / '.project').write_text('not a directory')
        before = tree(self.project)
        result = self.call()
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        self.assertIn('Path conflict', result.stderr)
        self.assertIn('.project', result.stderr)
        self.assertEqual(before, tree(self.project))

    def test_file_and_directory_conflicts_on_write_keep_state(self):
        (self.project / '.project').write_text('not a directory')
        self.assertEqual(1, self.call('--set', 'de').returncode)
        self.assertEqual('not a directory', (self.project / '.project').read_text())
        (self.project / '.project').unlink()
        self.stored().mkdir(parents=True)
        for args in ((), ('--set', 'de')):
            result = self.call(*args)
            self.assertEqual(1, result.returncode); self.assertEqual('', result.stdout)
        self.assertTrue(self.stored().is_dir())

    @unittest.skipIf(os.geteuid() == 0, 'permission checks need an unprivileged user')
    def test_read_error_is_not_reported_as_missing(self):
        self.assertEqual(0, self.call('--set', 'de').returncode)
        self.stored().chmod(0)
        result = self.call()
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        self.assertTrue(result.stderr.strip())

    @unittest.skipIf(os.geteuid() == 0, 'permission checks need an unprivileged user')
    def test_write_failure_reports_error_and_leaves_no_success_or_temp_files(self):
        self.assertEqual(0, self.call('--set', 'de').returncode)
        before = tree(self.project)
        (self.project / '.project').chmod(stat.S_IRUSR | stat.S_IXUSR)
        result = self.call('--set', 'en')
        (self.project / '.project').chmod(0o755)
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        self.assertEqual(before, tree(self.project))
        self.project.chmod(stat.S_IRUSR | stat.S_IXUSR)
        fresh = self.box.base / 'fresh'; fresh.mkdir(); fresh.chmod(stat.S_IRUSR | stat.S_IXUSR)
        result = self.call('--set', 'en', root=fresh)
        fresh.chmod(0o755); self.project.chmod(0o755)
        self.assertEqual((1, ''), (result.returncode, result.stdout))
        self.assertEqual({}, tree(fresh))

    def test_gitignore_is_never_touched(self):
        for existing in (None, 'custom\n'):
            root = self.box.base / ('with' if existing else 'without'); root.mkdir()
            if existing:
                (root / '.gitignore').write_text(existing)
            for args in ((), ('--set', 'de'), ('--set', 'de'), ('--set', 'en')):
                self.assertEqual(0, self.call(*args, root=root).returncode)
            self.assertEqual(existing, (root / '.gitignore').read_text() if existing else None)
            self.assertEqual(existing is not None, (root / '.gitignore').exists())

    def test_works_without_git_with_spaces_and_without_pythonpath(self):
        self.assertFalse(any((p / '.git').exists() for p in (self.project, *self.project.parents)[:3]))
        self.assertIn(' ', str(self.project)); self.assertIn(' ', str(self.helper))
        result = self.call('--set', 'de')  # PATH is empty and PYTHONPATH absent in run()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_helper_uses_only_standard_library_without_processes_or_network(self):
        tree_ = ast.parse((GENERATOR / HELPER).read_text())
        imported = {n.names[0].name.split('.')[0] for n in ast.walk(tree_) if isinstance(n, ast.Import)}
        imported |= {n.module.split('.')[0] for n in ast.walk(tree_) if isinstance(n, ast.ImportFrom)}
        self.assertEqual({'argparse', 'json', 'os', 'pathlib', 're', 'tempfile'}, imported)
        source = (GENERATOR / HELPER).read_text()
        for forbidden in ('subprocess', 'socket', 'urllib', 'os.system', 'shell=True', '/Users/', 'scripts/'):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
