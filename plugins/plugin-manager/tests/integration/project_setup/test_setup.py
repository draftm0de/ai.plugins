"""Project setup: status, supplementation, ownership lock, language and conflicts."""
import json
import os
import shutil
import stat
import unittest
from pathlib import Path
from unittest import mock

from tests.support import project_setup_fixture as fx
from tests.support.project_setup_fixture import FILES, LOCK, Sandbox, digest, pair, raw_pair, template, tree


class Base(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project

    def language_ok(self, tag):
        code, data, result = self.box.call('language', '--language', tag)
        self.assertEqual((0, True), (code, data['ok']), result.stderr + result.stdout)
        return data

    def setup_ok(self, *args):
        code, data, result = self.box.call('setup', *args)
        self.assertEqual((0, True), (code, data['ok']), result.stderr + result.stdout)
        return data


class StatusTests(Base):
    def test_status_is_write_free_and_separates_language_from_files(self):
        (self.p / 'AGENTS.md').write_bytes(b'custom')
        (self.p / 'scripts').mkdir()
        (self.p / 'scripts/plugin.py').write_bytes(template('scripts/plugin.py'))
        before, manager = tree(self.p), tree(self.box.manager)
        code, data, _ = self.box.call('status')
        self.assertEqual(0, code)
        self.assertEqual('identical', data['files']['scripts/plugin.py'])
        self.assertEqual('decision_needed', data['files']['AGENTS.md'])
        self.assertEqual('missing', data['files']['scripts/verify.py'])
        self.assertTrue(data['language']['needs_choice'])
        self.assertIn('scripts/plugin.py', data['lock']['pending'])
        self.assertFalse(data['matches_template'])
        self.assertEqual((before, manager), (tree(self.p), tree(self.box.manager)))  # no folders, lock, bytecode

    def test_status_with_stored_language_reports_it_without_writing(self):
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / '.project/operator.json').write_text('{"schema_version": 1, "operator_language": "en"}')
        before = tree(self.p)
        _, data, _ = self.box.call('status')
        self.assertEqual(('en', False), (data['language']['operator_language'], data['language']['needs_choice']))
        self.assertEqual(before, tree(self.p))


class SupplementTests(Base):
    def test_claude_copy_lock_and_preserve_local_changes(self):
        expected = template('CLAUDE.md')
        self.assertIn(b'This file exists only for Claude compatibility.', expected)
        self.assertEqual(b'@AGENTS.md', expected.split(b'-->')[1].strip())
        self.setup_ok('--language', 'de')
        target = self.p / 'CLAUDE.md'
        self.assertEqual(expected, target.read_bytes())
        self.assertEqual(pair(expected), self.box.lock()['CLAUDE.md'])
        target.write_bytes(b'local instructions')
        data = self.setup_ok()
        self.assertEqual(b'local instructions', target.read_bytes())
        self.assertIn('CLAUDE.md', data['different'])
        self.assertEqual(pair(expected), self.box.lock()['CLAUDE.md'])
        self.assertEqual(template('AGENTS.md'), (self.p / 'AGENTS.md').read_bytes())  # R28: the common instructions are managed
        self.assertFalse((self.p / 'CUSTOM.AGENTS.md').exists())  # the plugin's own file is seeded by the generator, never managed

    def test_creates_files_dirs_lock_and_modes_without_git(self):
        data = self.setup_ok('--language', 'de')
        for relative in FILES:
            self.assertEqual(template(relative), (self.p / relative).read_bytes())
            src = (fx.SHARED / 'templates/plugin/sync' / relative).stat().st_mode & 0o111
            self.assertEqual(bool(src), bool((self.p / relative).stat().st_mode & 0o111), relative)
        self.assertEqual({r: pair(template(r)) for r in FILES}, {k: v for k, v in self.box.lock().items() if k in FILES})
        self.assertTrue(set(FILES) <= set(data['created']['files']))  # delivery of the canonical templates
        self.assertTrue(data['matches_template'] and data['language']['saved'])
        self.assertFalse((self.p / '.git').exists())

    def test_repeat_writes_nothing(self):
        self.setup_ok('--language', 'de')
        stamps = {p: p.stat().st_mtime_ns for p in self.p.rglob('*') if p.is_file()}
        data = self.setup_ok()
        self.assertEqual(([], False, False), (data['created']['files'], data['lock']['changed'], data['gitignore']['changed']))
        self.assertEqual(stamps, {p: p.stat().st_mtime_ns for p in self.p.rglob('*') if p.is_file()})

    def test_identical_files_keep_mode_and_get_lock_evidence_fixed(self):
        (self.p / 'scripts').mkdir()
        target = self.p / 'scripts/verify.py'
        target.write_bytes(template('scripts/verify.py')); target.chmod(0o600)
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {'scripts/verify.py': raw_pair('0' * 64), 'other/x.txt': raw_pair('a' * 64)}}))
        self.setup_ok()
        self.assertEqual(0o600, stat.S_IMODE(target.stat().st_mode))
        self.assertEqual(pair(template('scripts/verify.py')), self.box.lock()['scripts/verify.py'])
        self.assertEqual(raw_pair('a' * 64), self.box.lock()['other/x.txt'])

    def test_different_files_are_kept_with_old_lock_and_others_supplemented(self):
        (self.p / 'AGENTS.md').write_bytes(b'mine')
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {'AGENTS.md': raw_pair('b' * 64)}}))
        data = self.setup_ok()
        self.assertEqual(b'mine', (self.p / 'AGENTS.md').read_bytes())
        self.assertEqual(raw_pair('b' * 64), self.box.lock()['AGENTS.md'])
        self.assertEqual(['AGENTS.md'], data['different'])
        self.assertFalse(data['matches_template'])
        self.assertTrue((self.p / 'scripts/plugin.py').is_file())

    def test_only_deviating_delivery_files_create_no_lock_for_them(self):
        for relative in FILES:
            path = self.p / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'x')
        data = self.setup_ok()
        self.assertTrue(set(FILES) <= set(data['different']))
        lock = self.box.lock() if (self.p / LOCK).exists() else {}
        self.assertFalse(set(FILES) & set(lock))  # no ownership evidence for deviating content (rules: test_sync)

    def test_resume_after_copy_without_lock(self):
        self.setup_ok('--language', 'de')
        (self.p / LOCK).unlink()
        data = self.setup_ok()
        self.assertTrue(data['lock']['changed'])
        self.assertTrue(set(FILES) <= set(self.box.lock()))

    def test_missing_file_with_lock_entry_is_recreated(self):
        self.setup_ok()
        (self.p / 'AGENTS.md').unlink()
        self.setup_ok()
        self.assertEqual(template('AGENTS.md'), (self.p / 'AGENTS.md').read_bytes())


class LanguageTests(Base):
    def test_rule_added_before_language_and_existing_ignore_kept(self):
        (self.p / '.gitignore').write_text('build/\n!keep\n')
        self.setup_ok('--language', 'en')
        self.assertEqual('build/\n!keep\n/.project/operator.json\n', (self.p / '.gitignore').read_text())
        self.setup_ok()
        self.assertEqual(1, (self.p / '.gitignore').read_text().count('/.project/operator.json'))

    def test_no_trailing_newline_and_rule_added_for_existing_preference(self):
        (self.p / '.gitignore').write_text('a')
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / '.project/operator.json').write_text('{"schema_version": 1, "operator_language": "de"}')
        self.setup_ok()
        self.assertEqual('a\n/.project/operator.json\n', (self.p / '.gitignore').read_text())
        self.assertEqual('de', json.loads((self.p / '.project/operator.json').read_text())['operator_language'])

    def test_order_ignore_before_language(self):
        order = []
        ps = fx.load_state(**self.box.ctx_args)
        real_ignore, real_load = ps.preferences.add_ignore_rule, ps.preferences.load_language_helper
        def ignore(*a):
            order.append('ignore'); return real_ignore(*a)
        def loader(ctx):
            helper = real_load(ctx); original = helper.preference
            helper.preference = lambda root, lang=None: (order.append('language') if lang else None, original(root, lang))[1]
            return helper
        with mock.patch.object(ps.preferences, 'add_ignore_rule', ignore), mock.patch.object(ps.preferences, 'load_language_helper', loader):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        self.assertEqual(['ignore', 'language'], order)

    def test_without_choice_no_language_or_ignore_written(self):
        data = self.setup_ok()
        self.assertTrue(data['language']['needs_choice'])
        self.assertFalse((self.p / '.project/operator.json').exists())
        self.assertFalse((self.p / '.gitignore').exists())

    def test_corrupt_language_blocks_all_writes(self):
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / '.project/operator.json').write_text('{broken')
        before = tree(self.p)
        code, data, _ = self.box.call('setup', '--language', 'de')
        self.assertEqual((1, False), (code, data['ok']))
        self.assertEqual(before, tree(self.p))

    def test_invalid_tag_and_conflicting_language_rejected_before_writes(self):
        before = tree(self.p)
        self.assertEqual(1, self.box.call('setup', '--language', 'Deutsch!')[0])
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / '.project/operator.json').write_text('{"schema_version": 1, "operator_language": "de"}')
        before = tree(self.p)
        self.assertEqual(1, self.box.call('setup', '--language', 'en')[0])
        self.assertEqual(before, tree(self.p))


class ConflictTests(Base):
    def assert_blocked(self, *args, reason=None):
        before = tree(self.p)
        code, data, _ = self.box.call('setup', '--language', 'de', *args)
        self.assertEqual((1, False), (code, data['ok']))
        self.assertTrue(data['conflicts'])
        if reason:
            self.assertIn(reason, data['conflicts'][0]['reason'])
        self.assertEqual(before, tree(self.p))
        return data

    def test_lock_problems(self):
        (self.p / '.project').mkdir(exist_ok=True)
        lock = self.p / LOCK
        for text in ('{bad', '{"schema_version": 3, "files": {}}', '{"schema_version": true, "files": {}}',
                     '{"schema_version": 1, "files": {"a": "ABC"}}', '{"schema_version": 1, "files": {"../x": "%s"}}' % ('a' * 64),
                     '{"schema_version": 1, "files": {}, "files": {}}',
                     '{"schema_version": 1, "files": {"a": "%s", "a": "%s"}}' % ('a' * 64, 'b' * 64),
                     '{"schema_version": 1, "files": {}, "extra": 1}',
                     '{"schema_version": 1, "files": {"install.sh": "%s"}}' % ('a' * 64),  # valid v1: no migration
                     '{"schema_version": 2, "files": {"install.sh": "%s"}}' % ('a' * 64),
                     '{"schema_version": 2, "files": {"install.sh": {"source_hash": "ABC", "local_hash": "%s"}}}' % ('a' * 64),
                     '{"schema_version": 2, "files": {"install.sh": {"source_hash": "%s"}}}' % ('a' * 64),
                     '{"schema_version": 2, "files": {"../x": {"source_hash": "%s", "local_hash": "%s"}}}' % ('a' * 64, 'a' * 64)):
            with self.subTest(text=text):
                lock.write_text(text)
                self.assert_blocked()

    def test_file_dir_conflicts_and_symlinks(self):
        (self.p / 'scripts').write_text('file instead of folder')
        self.assert_blocked()
        (self.p / 'scripts').unlink()
        (self.p / 'AGENTS.md').mkdir()
        self.assert_blocked()
        (self.p / 'AGENTS.md').rmdir()
        outside = self.box.base / 'outside'; outside.mkdir()
        (self.p / 'scripts').symlink_to(outside)
        self.assert_blocked(reason='Symlink')
        self.assertEqual([], list(outside.iterdir()))

    def test_symlinked_gitignore_project_and_lock(self):
        (self.p / 'x').write_text('x')
        (self.p / '.gitignore').symlink_to(self.p / 'x')
        self.assert_blocked()
        (self.p / '.gitignore').unlink()
        shutil.rmtree(self.p / '.project')
        (self.p / '.project').symlink_to(self.box.base)
        self.assert_blocked()

    def test_unreadable_file(self):
        (self.p / 'AGENTS.md').write_bytes(b'x'); (self.p / 'AGENTS.md').chmod(0)
        if os.geteuid() == 0:
            self.skipTest('root can read everything')
        self.assert_blocked(reason='Cannot read')

    def test_invalid_template_source_or_base_is_a_conflict_not_a_removal(self):
        base = self.box.manager / 'skills/_shared/templates/plugin/sync'
        (base / 'AGENTS.md').unlink()
        (base / 'AGENTS.md').symlink_to(self.box.base)  # a link is never "removed"
        self.assert_blocked(reason='Template')
        (base / 'AGENTS.md').unlink()
        (base / 'AGENTS.md').mkdir()  # wrong type
        self.assert_blocked(reason='Template')
        (base / 'AGENTS.md').rmdir()
        shutil.rmtree(base)  # whole template base missing
        self.assert_blocked(reason='Template base')

    def test_non_targets(self):
        for build, text in ((lambda: (self.p / 'marketplace.json').write_text('{}'), 'marketplace.json'),
                            (lambda: (self.p / 'plugin.json').write_text('{"name": "Bad Name"}'), 'name'),
                            (lambda: (self.p / 'plugin.json').write_text('{"name": "a", "name": "b"}'), 'Invalid')):
            build()
            self.assert_blocked(reason=text)
            (self.p / 'marketplace.json').unlink(missing_ok=True)
            (self.p / 'plugin.json').write_text('{"name": "demo-plugin"}')
        code, data, _ = self.box.call('setup', target=self.box.manager)
        self.assertEqual(1, code)
        empty = self.box.base / 'empty'; empty.mkdir()
        self.assertEqual(0, self.box.call('status', target=empty)[0])  # unconfigured but initializable, see test_fresh
        self.assertEqual(1, self.box.call('status', target=self.box.base / 'nope')[0])
        link = self.box.base / 'link'; link.symlink_to(self.p)
        self.assertEqual(1, self.box.call('status', target=link)[0])

    def test_missing_dev_files_do_not_block_detection(self):
        self.assertEqual(0, self.box.call('status')[0])

    def test_file_appearing_during_copy_is_not_overwritten(self):
        ps = fx.load_state(**self.box.ctx_args)
        real = ps.fsafe.copy_new
        def racing(path, data, executable):
            if path.name == 'run_tests.py':
                path.write_bytes(b'foreign')
            return real(path, data, executable)
        with mock.patch.object(ps.fsafe, 'copy_new', racing):
            data = ps.setup(str(self.p), 'de')
        self.assertEqual(b'foreign', (self.p / 'scripts/run_tests.py').read_bytes())
        self.assertIn('scripts/run_tests.py', data['different'])
        self.assertNotIn('scripts/run_tests.py', self.box.lock())

    def test_write_failure_reports_partial_changes_and_resume_works(self):
        ps = fx.load_state(**self.box.ctx_args)
        real = ps.fsafe.copy_new
        def failing(path, data, executable):
            if path.name == 'verify.py':
                raise OSError('disk full')
            return real(path, data, executable)
        with mock.patch.object(ps.fsafe, 'copy_new', failing):
            data = ps.setup(str(self.p), 'de')
        self.assertFalse(data['ok'])
        self.assertIn('scripts/plugin.py', data['created']['files'])
        self.assertFalse((self.p / LOCK).exists())
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertTrue(set(FILES) <= set(self.box.lock()))


class BoundaryTests(Base):
    def test_other_project_files_and_target_code_untouched(self):
        owned = {'AGENTS.md': b'a', 'CLAUDE.md': b'c', 'Makefile': b'm', 'ci.yml': b'y', 'SCOPE.md': b's',
                 'skills/x/SKILL.md': b'k', 'skills/x/scripts/run.py': b'raise SystemExit(9)'}
        for name, data in owned.items():
            path = self.p / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        manifest = (self.p / 'plugin.json').read_bytes()
        self.setup_ok('--language', 'de')
        for name, data in owned.items():
            self.assertEqual(data, (self.p / name).read_bytes())
        self.assertEqual(manifest, (self.p / 'plugin.json').read_bytes())
        self.assertEqual(['tests/behavior/run_cases.py', 'tests/contracts/test_operator_language.py'], sorted(str(p.relative_to(self.p)) for p in (self.p / 'tests').rglob('*') if p.is_file()))  # only the managed runner

    def test_runs_from_complete_isolated_manager_copy_with_no_bytecode_and_no_network_modules(self):
        manager = tree(self.box.manager)
        self.setup_ok('--language', 'de')
        self.assertEqual(manager, tree(self.box.manager))
        source = '\n'.join(path.read_text() for path in sorted(fx.SETUP_SCRIPTS.rglob('*.py')))
        for forbidden in ('socket', 'urllib', 'subprocess', 'import scripts', 'from scripts', '/Users/'):
            self.assertNotIn(forbidden, source)


class RaceTests(Base):
    def module(self, name):
        return fx.load_state(**self.box.ctx_args)

    def after_snapshot(self, ps, change):
        real = ps.inspection.inspect
        def inspect(*args):
            plan = real(*args); change(); return plan
        return mock.patch.object(ps.inspection, 'inspect', inspect)

    def test_gitignore_changed_after_snapshot_is_not_lost(self):
        ps = self.module('race1')
        (self.p / '.gitignore').write_text('old\n')
        with self.after_snapshot(ps, lambda: (self.p / '.gitignore').write_text('old\nnew-rule\n')):
            data = ps.setup(str(self.p), 'de')
        self.assertTrue(data['ok'])
        self.assertEqual('old\nnew-rule\n/.project/operator.json\n', (self.p / '.gitignore').read_text())

    def test_gitignore_created_after_snapshot_is_extended_not_replaced(self):
        ps = self.module('race2')
        with self.after_snapshot(ps, lambda: (self.p / '.gitignore').write_text('foreign\n')):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        self.assertEqual('foreign\n/.project/operator.json\n', (self.p / '.gitignore').read_text())

    def test_gitignore_changed_between_read_and_replace_retries_on_fresh_content(self):
        ps = self.module('race3')
        (self.p / '.gitignore').write_text('a\n')
        real, calls = ps.fsafe.current_bytes, []
        def current(path):
            if path.name == '.gitignore' and not calls:
                calls.append(1); path.write_text('a\nb\n')
            return real(path)
        with mock.patch.object(ps.fsafe, 'current_bytes', current):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        self.assertEqual('a\nb\n/.project/operator.json\n', (self.p / '.gitignore').read_text())

    def test_lock_changed_after_snapshot_keeps_foreign_entries(self):
        ps = self.module('race4')
        def change():
            (self.p / '.project').mkdir(exist_ok=True)
            (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {'foreign/x': raw_pair('c' * 64)}}))
        with self.after_snapshot(ps, change):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        lock = self.box.lock()
        self.assertEqual(raw_pair('c' * 64), lock['foreign/x'])
        self.assertTrue(set(FILES) | {'foreign/x'} <= set(lock))

    def test_lock_changed_between_read_and_replace_retries(self):
        ps = self.module('race5')
        real, calls = ps.fsafe.current_bytes, []
        def current(path):
            if path.name == 'skeleton.json' and not calls:
                calls.append(1)
                path.write_text(json.dumps({'schema_version': 2, 'files': {'late': raw_pair('d' * 64)}}))
            return real(path)
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {}}))
        with mock.patch.object(ps.fsafe, 'current_bytes', current):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        self.assertIn('late', self.box.lock())

    def test_lock_made_invalid_meanwhile_is_not_overwritten(self):
        ps = self.module('race6')
        def change():
            (self.p / '.project').mkdir(exist_ok=True)
            (self.p / LOCK).write_text('{broken')
        with self.after_snapshot(ps, change):
            data = ps.setup(str(self.p), 'de')
        self.assertFalse(data['ok'])
        self.assertEqual('{broken', (self.p / LOCK).read_text())

    def appear_as(self, make, name):
        ps = self.module(name)
        reads = []
        real_read = Path.read_bytes
        def read(path):
            reads.append(path); return real_read(path)
        real_copy = ps.fsafe.copy_new
        def racing(path, data, executable):
            if path.name == 'run_tests.py':
                make(path)
            return real_copy(path, data, executable)
        with mock.patch.object(ps.fsafe, 'copy_new', racing), mock.patch.object(Path, 'read_bytes', read):
            data = ps.setup(str(self.p), 'de')
        return data, reads

    def test_symlink_appearing_at_target_is_not_followed_or_read(self):
        secret = self.box.base / 'secret.txt'; secret.write_bytes(b'private')
        data, reads = self.appear_as(lambda path: path.symlink_to(secret), 'race7')
        target = self.p / 'scripts/run_tests.py'
        self.assertFalse(data['ok'])
        self.assertIn('Symlink', data['conflicts'][0]['reason'])
        self.assertEqual('conflict', data['files']['scripts/run_tests.py'])
        self.assertNotIn(target, reads)
        self.assertNotIn(secret, reads)
        self.assertTrue(target.is_symlink())
        self.assertEqual(b'private', secret.read_bytes())
        self.assertFalse((self.p / LOCK).exists())  # no ownership claim after an unsafe entry

    def test_directory_appearing_at_target_is_reported_not_read(self):
        data, reads = self.appear_as(lambda path: path.mkdir(), 'race8')
        self.assertFalse(data['ok'])
        self.assertNotIn(self.p / 'scripts/run_tests.py', reads)


class SnapshotTests(Base):
    def test_lock_change_between_parse_and_raw_read_cannot_drop_entries(self):
        """Validated lock and expected bytes come from one read; a later change forces a retry."""
        ps = fx.load_state(**self.box.ctx_args)
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {}}))
        real, calls = ps.fsafe.read_regular, []
        def reading(root, relative):
            data = real(root, relative)
            if relative == LOCK and len(calls) == 1:  # first read inside write_lock (after planning read)
                (self.p / LOCK).write_text(json.dumps({'schema_version': 2, 'files': {'late': raw_pair('e' * 64)}}))
            if relative == LOCK:
                calls.append(1)
            return data
        with mock.patch.object(ps.fsafe, 'read_regular', reading):
            self.assertTrue(ps.setup(str(self.p), 'de')['ok'])
        lock = self.box.lock()
        self.assertEqual(raw_pair('e' * 64), lock['late'])
        self.assertTrue(set(FILES) <= set(lock))

    def test_identical_file_changed_after_classification_gets_no_hash(self):
        ps = fx.load_state(**self.box.ctx_args)
        (self.p / 'scripts').mkdir()
        target = self.p / 'scripts/plugin.py'
        target.write_bytes(template('scripts/plugin.py'))
        real = ps.inspection.inspect
        def inspect(*args):
            plan = real(*args); target.write_bytes(b'changed meanwhile'); return plan
        with mock.patch.object(ps.inspection, 'inspect', inspect):
            data = ps.setup(str(self.p), 'de')
        self.assertTrue(data['ok'])
        self.assertEqual(b'changed meanwhile', target.read_bytes())
        self.assertNotIn('scripts/plugin.py', self.box.lock())
        self.assertIn('scripts/plugin.py', data['different'])
        self.assertFalse(data['matches_template'])


class TechnicalErrorTests(Base):
    """Technical failures are never reported as content deviations; progress stays visible."""
    def module(self, name):
        return fx.load_state(**self.box.ctx_args)

    def run_with_change(self, name, change, language='de'):
        ps = self.module(name)
        real = ps.inspection.inspect
        def inspect(*args):
            plan = real(*args); change(); return plan
        with mock.patch.object(ps.inspection, 'inspect', inspect):
            return ps.setup(str(self.p), language)

    def preidentical(self):
        (self.p / 'scripts').mkdir()
        target = self.p / 'scripts/plugin.py'
        target.write_bytes(template('scripts/plugin.py'))
        return target

    def assert_technical(self, data, relative='scripts/plugin.py'):
        self.assertFalse(data['ok'])
        self.assertTrue(data['conflicts'])
        self.assertNotIn(relative, data['different'])
        self.assertEqual('conflict', data['files'][relative])
        self.assertFalse(data['matches_template'])
        self.assertFalse((self.p / LOCK).exists())  # no ownership evidence after a technical error

    def test_identical_file_replaced_by_symlink_is_a_conflict_not_a_deviation(self):
        target = self.preidentical()
        outside = self.box.base / 'outside.py'; outside.write_bytes(b'x')
        def change():
            target.unlink(); target.symlink_to(outside)
        data = self.run_with_change('t1', change)
        self.assert_technical(data)
        self.assertEqual(b'x', outside.read_bytes())

    def test_identical_file_replaced_by_directory_is_a_conflict(self):
        target = self.preidentical()
        def change():
            target.unlink(); target.mkdir()
        self.assert_technical(self.run_with_change('t2', change))

    @unittest.skipIf(os.geteuid() == 0, 'root can read everything')
    def test_identical_file_becoming_unreadable_is_a_conflict(self):
        target = self.preidentical()
        self.assert_technical(self.run_with_change('t3', lambda: target.chmod(0)))

    def test_plain_byte_change_stays_an_allowed_deviation(self):
        target = self.preidentical()
        data = self.run_with_change('t4', lambda: target.write_bytes(b'edited'))
        self.assertTrue(data['ok'])
        self.assertIn('scripts/plugin.py', data['different'])
        self.assertNotIn('scripts/plugin.py', self.box.lock())

    def test_late_gitignore_conflict_keeps_progress_report(self):
        outside = self.box.base / 'ignore-target'; outside.write_text('x\n')
        data = self.run_with_change('t5', lambda: (self.p / '.gitignore').symlink_to(outside))
        self.assertFalse(data['ok'])
        self.assertEqual('.gitignore', data['conflicts'][0]['path'])
        self.assertIn('scripts', data['created']['directories'])  # folders created before the conflict
        self.assertEqual('x\n', outside.read_text())
        self.assertFalse((self.p / LOCK).exists())

    def test_verification_failure_after_creation_reports_unverified_file_without_hash(self):
        ps = self.module('t6')
        real = ps.fsafe.copy_new
        def corrupt(path, data, executable):
            return real(path, b'corrupt' if path.name == 'verify.py' else data, executable)
        with mock.patch.object(ps.fsafe, 'copy_new', corrupt):
            data = ps.setup(str(self.p), 'de')
        self.assertFalse(data['ok'])
        self.assertIn('scripts/verify.py', data['created']['files'])
        self.assertEqual(['scripts/verify.py'], data['created']['unverified'])
        self.assertEqual('unverified', data['files']['scripts/verify.py'])
        self.assertFalse((self.p / LOCK).exists())
        resumed = self.setup_ok()  # a later run keeps the unverified file as a plain deviation
        self.assertIn('scripts/verify.py', resumed['different'])

    def test_language_save_failure_after_project_folder_creation_is_reported(self):
        shutil.rmtree(self.p / '.project')  # unconfigured: only the language step writes here (R17)
        ps = self.module('t7')
        real = ps.preferences.load_language_helper
        def loader(ctx):
            helper = real(ctx); original = helper.preference
            def preference(root, language=None):
                if language:
                    (Path(root) / '.project').mkdir(exist_ok=True)
                    raise OSError('disk full')
                return original(root, language)
            helper.preference = preference
            return helper
        with mock.patch.object(ps.preferences, 'load_language_helper', loader):
            data = ps.language_only(str(self.p), 'de')
        self.assertFalse(data['ok'])
        self.assertIn('.project', data['created']['directories'])
        self.assertFalse(data['language']['saved'])
        self.assertTrue(data['gitignore']['changed'])  # ignore rule was written before the failed save

    def test_status_reports_missing_management_folder(self):
        shutil.rmtree(self.p / '.project')  # no evidence yet: the management folder is missing
        _, data, _ = self.box.call('status')
        self.assertIn('.project', data['missing']['directories'])
        self.language_ok('de')
        _, data, _ = self.box.call('status')
        self.assertNotIn('.project', data['missing']['directories'])

    def test_language_helper_created_folder_is_listed_on_success(self):
        shutil.rmtree(self.p / '.project')
        data = self.language_ok('de')
        self.assertIn('.project', data['created']['directories'])

    @unittest.skipIf(os.geteuid() == 0, 'root ignores permissions')
    def test_unsearchable_parent_gives_structured_exit_one_without_writes(self):
        (self.p / 'scripts').mkdir()
        (self.p / 'scripts').chmod(0)
        before = {p.name for p in self.p.iterdir()}
        for operation in ('status', 'setup'):
            with self.subTest(operation=operation):
                code, data, result = self.box.call(operation)
                self.assertEqual((1, False), (code, data['ok']), result.stderr)
                self.assertIn('Cannot inspect', data['conflicts'][0]['reason'])
                self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(before, {p.name for p in self.p.iterdir()})

    def test_oserror_outside_write_phase_is_structured(self):
        ps = self.module('t8')
        with mock.patch.object(ps.reporting, 'status', side_effect=PermissionError(13, 'Permission denied')):
            import io, contextlib
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = ps.main(['status', '--target', str(self.p), '--plugin', fx.PLUGIN])
        self.assertEqual(1, code)
        self.assertIn('Filesystem error', json.loads(out.getvalue())['conflicts'][0]['reason'])


class TemplateAndIdentityTests(Base):
    def test_symlinked_template_parent_is_rejected_without_reading_linked_content(self):
        ps = fx.load_state(**self.box.ctx_args)
        templates = self.box.manager / 'skills/_shared/templates/plugin/sync'
        outside = self.box.base / 'linked-scripts'
        (templates / 'scripts').rename(outside)
        (templates / 'scripts').symlink_to(outside)
        reads = []
        real = Path.read_bytes
        def read(path):
            reads.append(path); return real(path)
        before = tree(self.p)
        with mock.patch.object(Path, 'read_bytes', read):
            with self.assertRaises(ps.Conflict) as caught:
                ps.setup(str(self.p), 'de')
        self.assertIn('Symlink', caught.exception.reason)
        self.assertFalse([r for r in reads if 'linked-scripts' in str(r) or r.parts[-2:-1] == ('scripts',)])
        self.assertEqual(before, tree(self.p))
        code, data, _ = self.box.call('setup', '--language', 'de')  # CLI form
        self.assertEqual((1, False), (code, data['ok']))
        self.assertEqual(before, tree(self.p))

    def test_embedded_manager_is_rejected_by_identity(self):
        code, data, _ = self.box.call('status', target=fx.ROOT, real=True)
        self.assertEqual((1, False), (code, data['ok']))
        self.assertIn('embedded Plugin Manager', data['conflicts'][0]['reason'])
        (self.p / 'plugin.json').write_text('{"name": "plugin-manager"}')  # same identity elsewhere
        self.assertEqual(1, self.box.call('status')[0])

    def test_manager_root_constant_points_at_plugin_root(self):
        self.assertEqual(fx.ROOT, fx.load_state().ctx.manager_root)

    def test_other_plugin_with_own_template_folder_is_a_valid_target(self):
        own = self.p / 'skills/_shared/templates/plugin'
        own.mkdir(parents=True); (own / 'x.txt').write_text('own')
        code, data, _ = self.box.call('status')
        self.assertEqual((0, True), (code, data['ok']))
        self.setup_ok('--language', 'de')
        self.assertEqual('own', (own / 'x.txt').read_text())
