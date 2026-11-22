"""Removal of managed files whose source disappeared from the parent, on a minimal FICTIONAL parent.

Real project_setup.py and operator_language.py run unchanged; only the managed list of the copied script is the
fixed fictional one from the fixture. Expectations use literal bytes and hashlib, never production templates.
Removing a source means deleting its file from the fictional parent copy."""
import json
import os
import shutil
import unittest
from unittest import mock

from tests.support.workflow_fixture import WorkflowFixture  # puts the Manager scripts on sys.path
from tests.integration.project_setup.test_setup import load_module
from tests.support import project_setup_fixture as fx
from tests.support.project_setup_fixture import (ALPHA, BETA, DELTA, FICTIONAL, GAMMA, LOCK, ZETA, FictionalSandbox,
                                                 digest, tree)

GONE = 'alpha.md'
OTHER = 'delta.md'
DOCS = 'docs/beta.txt'        # sibling docs/zeta.txt keeps the folder needed
DEEP = 'tools/deep/gamma.sh'  # sole file of two nested folders


def pair(source, local=None):
    return {'source_hash': digest(source), 'local_hash': digest(source if local is None else local)}


class RemovalBase(unittest.TestCase):
    def setUp(self):
        self.box = FictionalSandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        self.assertEqual(0, self.box.call('setup')[0])

    def drop_source(self, relative=GONE):
        self.box.drop_template(relative)

    def restore_source(self, relative=GONE):
        self.box.set_template(relative, FICTIONAL[relative][0])

    def status(self):
        code, data, _ = self.box.call('status')
        self.assertEqual(0, code, data)
        return data

    def lock(self):
        return json.loads((self.p / LOCK).read_text())['files']

    def decide(self, decision, relative=GONE, expect=True):
        item = next(d for d in self.status()['removals']['decisions'] if d['path'] == relative)
        code, data, result = self.box.call('sync', '--decision', decision, '--path', relative,
                                           '--source-hash', item['source_hash'] or 'removed', '--local-hash', item['local_hash'])
        self.assertEqual(expect, code == 0 and data['ok'], (data, result.stderr))
        return data


class AutomaticRemovalTests(RemovalBase):
    def test_template_identical_owned_file_is_removed_with_its_lock_entry(self):
        self.drop_source()
        before = tree(self.p)
        status = self.status()
        self.assertEqual(('skeleton', [GONE], [], []), (status['next'], status['removals']['auto'],
                                                     status['removals']['decisions'], status['removals']['kept']))
        self.assertEqual(before, tree(self.p))  # status is absolutely write-free
        code, data, _ = self.box.call('setup')
        self.assertEqual((0, True, [GONE]), (code, data['ok'], data['removed']['files']))
        self.assertFalse((self.p / GONE).exists())
        self.assertNotIn(GONE, self.lock())
        after = self.status()
        self.assertEqual(('ready', True), (after['next'], after['matches_template']))
        snapshot = tree(self.p)
        self.assertEqual(0, self.box.call('setup')[0])  # repetition writes nothing
        self.assertEqual(snapshot, tree(self.p))

    def test_modified_or_accepted_local_file_is_never_removed_automatically(self):
        (self.p / GONE).write_bytes(b'my notes')  # local change
        (self.p / OTHER).write_bytes(b'accepted local variant')
        item = next(d for d in self.status()['sync']['decisions'] if d['path'] == OTHER)
        self.assertEqual(0, self.box.call('sync', '--decision', 'keep', '--path', OTHER,
                                          '--source-hash', item['source_hash'], '--local-hash', item['local_hash'])[0])
        self.drop_source(GONE); self.drop_source(OTHER)
        status = self.status()
        self.assertEqual([], status['removals']['auto'])
        self.assertEqual({GONE, OTHER}, {d['path'] for d in status['removals']['decisions']})
        self.assertEqual('sync', status['next'])
        self.box.call('setup')
        self.assertEqual(b'my notes', (self.p / GONE).read_bytes())
        self.assertEqual(b'accepted local variant', (self.p / OTHER).read_bytes())

    def test_without_ownership_evidence_nothing_is_ever_deleted(self):
        (self.p / LOCK).unlink()
        self.drop_source()
        status = self.status()
        self.assertEqual(([GONE], [], 'skeleton'), (status['removals']['unowned'], status['removals']['auto'], status['next']))  # other files lack pairs
        self.box.call('setup')
        self.assertEqual(ALPHA, (self.p / GONE).read_bytes())
        self.assertNotIn(GONE, self.lock())
        self.assertEqual(([GONE], 'ready'), (self.status()['removals']['unowned'], self.status()['next']))
        self.assertFalse(self.status()['matches_template'])

    def test_locally_missing_file_only_cleans_the_lock_and_keeps_other_entries(self):
        self.drop_source()
        (self.p / GONE).unlink()
        data = json.loads((self.p / LOCK).read_text())
        data['files']['elsewhere/unmanaged.txt'] = pair(b'x')
        (self.p / LOCK).write_text(json.dumps(data))
        os.makedirs(self.p / 'elsewhere'); (self.p / 'elsewhere/unmanaged.txt').write_text('x')
        status = self.status()
        self.assertEqual(([GONE], 'skeleton'), (status['removals']['lock_cleanup'], status['next']))
        self.assertEqual(0, self.box.call('setup')[0])
        lock = self.lock()
        self.assertNotIn(GONE, lock)
        self.assertEqual(pair(b'x'), lock['elsewhere/unmanaged.txt'])  # unmanaged entries stay unchanged
        self.assertEqual('ready', self.status()['next'])


class DecisionTests(RemovalBase):
    def modified(self):
        (self.p / GONE).write_bytes(b'my notes')
        self.drop_source()

    def test_keep_persists_source_null_and_stops_asking_until_the_file_changes_again(self):
        self.modified()
        item = self.status()['removals']['decisions'][0]
        self.assertEqual(('source_removed_local_differs', None, True), (item['reason'], item['source_hash'], item['source_removed']))
        data = self.decide('keep')
        self.assertEqual((True, 'status'), (data['changed']['lock'], data['next']))
        self.assertEqual({'source_hash': None, 'local_hash': digest(b'my notes')}, self.lock()[GONE])
        self.assertEqual(b'my notes', (self.p / GONE).read_bytes())
        status = self.status()
        self.assertEqual(([GONE], [], 'ready', False), (status['removals']['kept'], status['removals']['decisions'],
                                                      status['next'], status['matches_template']))
        snapshot = tree(self.p)
        for _ in range(2):
            self.box.call('setup'); self.status()
        self.assertEqual(snapshot, tree(self.p))  # unchanged repetition: no question, no write
        (self.p / GONE).write_bytes(b'changed again')
        self.assertEqual('source_removed_local_changed', self.status()['removals']['decisions'][0]['reason'])

    def test_explicit_delete_removes_file_and_lock_entry_only(self):
        self.modified()
        data = self.decide('delete')
        self.assertEqual(([GONE], True, True), (data['removed']['files'], data['changed']['file'], data['changed']['lock']))
        self.assertFalse((self.p / GONE).exists())
        self.assertNotIn(GONE, self.lock())
        self.assertEqual(DELTA, (self.p / OTHER).read_bytes())
        self.assertEqual('ready', self.status()['next'])

    def test_cancelled_or_unanswered_question_persists_nothing(self):
        self.modified()
        before = tree(self.p)
        for _ in range(3):
            self.assertEqual('sync', self.status()['next'])
        self.assertEqual(before, tree(self.p))

    def test_returning_source_is_classified_normally_again(self):
        self.modified(); self.decide('keep')
        self.restore_source()
        status = self.status()  # local differs from the returned source and the stored pair has no source
        self.assertEqual(([], 'sync', 'source_changed'), (status['removals']['kept'], status['next'], status['sync']['decisions'][0]['reason']))
        (self.p / GONE).write_bytes(ALPHA)  # local equals the returned source: pair corrected without a dialogue
        status = self.status()
        self.assertEqual(('skeleton', False), (status['next'], status['sync']['needed']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(pair(ALPHA), self.lock()[GONE])

    def test_stale_wrong_kind_and_hash_forms_are_rejected_without_writes(self):
        self.modified()
        item = self.status()['removals']['decisions'][0]
        before = tree(self.p)
        base = ('sync', '--path', GONE)
        cases = [
            (('--decision', 'adopt', '--source-hash', 'removed', '--local-hash', item['local_hash']), 'invalid_decision'),
            (('--decision', 'delete', '--source-hash', digest(b'x'), '--local-hash', item['local_hash']), 'stale_decision'),
            (('--decision', 'delete', '--source-hash', 'removed', '--local-hash', digest(b'other')), 'stale_decision'),
            (('--decision', 'delete', '--source-hash', 'REMOVED', '--local-hash', item['local_hash']), 'invalid_hash'),
        ]
        for args, code in cases:
            c, data, _ = self.box.call(*base, *args)
            self.assertEqual((1, code), (c, data['conflicts'][0]['code']))
            self.assertEqual(before, tree(self.p))
        (self.p / OTHER).write_bytes(b'x')  # a content question does not accept delete
        shown = next(d for d in self.status()['sync']['decisions'] if d['path'] == OTHER)
        c, data, _ = self.box.call('sync', '--decision', 'delete', '--path', OTHER, '--source-hash', shown['source_hash'], '--local-hash', shown['local_hash'])
        self.assertEqual((1, 'invalid_decision'), (c, data['conflicts'][0]['code']))
        self.assertTrue((self.p / OTHER).exists())

    def test_status_output_carries_hashes_and_paths_but_no_file_content(self):
        (self.p / GONE).write_bytes(b'SECRET-CONTENT-MARKER')
        self.drop_source()
        code, data, result = self.box.call('status')
        self.assertNotIn('SECRET-CONTENT-MARKER', result.stdout)
        self.assertNotIn(DELTA.decode()[:8], result.stdout)


class FolderTests(RemovalBase):
    def test_empty_parents_go_bottom_up_but_needed_folders_stay(self):
        self.drop_source(DEEP)
        data = self.box.call('setup')[1]
        self.assertEqual(([DEEP], ['tools/deep', 'tools']), (data['removed']['files'], data['removed']['directories']))
        self.assertFalse((self.p / 'tools').exists())
        self.drop_source(DOCS)
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertTrue((self.p / 'docs').is_dir())  # docs/zeta.txt still has a present source
        self.assertEqual(ZETA, (self.p / 'docs/zeta.txt').read_bytes())
        for protected in ('.project', LOCK):
            self.assertTrue((self.p / protected).exists())

    def test_foreign_content_keeps_the_folder_and_is_never_deleted(self):
        (self.p / 'tools/deep/own-notes.md').write_text('mine')
        self.drop_source(DEEP)
        data = self.box.call('setup')[1]
        self.assertEqual(([DEEP], []), (data['removed']['files'], data['removed']['directories']))
        self.assertEqual('mine', (self.p / 'tools/deep/own-notes.md').read_text())

    def test_root_git_idea_and_project_are_never_removed(self):
        for name in ('.git', '.idea'):
            (self.p / name).mkdir(); (self.p / name / 'x').write_text('x')
        self.drop_source(GONE)
        self.assertEqual(0, self.box.call('setup')[0])
        for protected in (self.p, self.p / '.git/x', self.p / '.idea/x', self.p / '.project'):
            self.assertTrue(protected.exists())

    def test_a_returning_source_recreates_folder_and_file(self):
        self.drop_source(DEEP)
        self.assertEqual(0, self.box.call('setup')[0])
        self.restore_source(DEEP)
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(GAMMA, (self.p / DEEP).read_bytes())
        self.assertEqual(pair(GAMMA), self.lock()[DEEP])


class SourceBaseTests(RemovalBase):
    def blocked(self, expect_code=None):
        before = tree(self.p)
        for args in (('status',), ('setup',)):
            code, data, _ = self.box.call(*args)
            self.assertEqual((1, 'stop'), (code, data['next']), args)
            if expect_code:
                self.assertEqual(expect_code, data['conflicts'][0].get('code'))
            self.assertEqual(before, tree(self.p))

    def test_missing_base_all_sources_missing_and_unsafe_paths_never_mean_removal(self):
        base = self.box.manager / 'skills/_shared/templates/plugin/sync'
        saved = self.box.base / 'saved-templates'
        shutil.move(str(base), str(saved))
        self.blocked('template_base')
        base.mkdir(parents=True)  # base exists but holds no managed source at all
        self.blocked('template_base')
        shutil.rmtree(base); shutil.copytree(saved, base)
        (base / 'docs').rename(self.box.base / 'moved-docs')
        (base / 'docs').symlink_to(self.box.base / 'moved-docs')  # symlinked parent of sources
        self.blocked()
        self.assertEqual(DELTA, (self.p / OTHER).read_bytes())
        self.assertEqual(BETA, (self.p / DOCS).read_bytes())

    def test_unsafe_local_path_of_a_removed_source_blocks_before_any_delete(self):
        self.drop_source()
        (self.p / GONE).unlink()
        (self.p / GONE).symlink_to(self.box.base)
        self.blocked()
        self.assertTrue((self.p / GONE).is_symlink())


class PartialFailureTests(RemovalBase):
    def test_failure_after_first_removal_reports_actual_changes_and_resume_heals(self):
        self.drop_source(OTHER); self.drop_source(GONE)
        ps = load_module(self.box.helper, 'removal_partial')
        real, calls = ps.remove_managed_file, []
        def failing(*args, **kw):
            calls.append(args[1])
            if len(calls) == 2:
                raise OSError('device busy')
            return real(*args, **kw)
        with mock.patch.object(ps, 'remove_managed_file', failing):
            data = ps.setup(str(self.p))
        self.assertFalse(data['ok'])
        self.assertEqual(1, len(data['removed']['files']))
        gone = data['removed']['files'][0]
        kept = next(r for r in (OTHER, GONE) if r != gone)
        self.assertFalse((self.p / gone).exists())
        self.assertTrue((self.p / kept).exists())
        self.assertIn(gone, self.lock())  # lock not written after the error ...
        status = self.status()  # ... and the next status heals: cleanup of the vanished file, removal of the other
        self.assertEqual(([gone], [kept]), (status['removals']['lock_cleanup'], status['removals']['auto']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(('ready', set(FICTIONAL) - {GONE, OTHER}), (self.status()['next'], set(self.lock())))

    def test_changed_file_at_delete_time_is_a_conflict_without_deletion(self):
        self.drop_source()
        ps = load_module(self.box.helper, 'removal_changed')
        real = ps.inspect
        def inspect(*a):
            plan = real(*a); (self.p / GONE).write_bytes(b'edited after the check'); return plan
        with mock.patch.object(ps, 'inspect', inspect):
            data = ps.setup(str(self.p))
        self.assertFalse(data['ok'])
        self.assertEqual(b'edited after the check', (self.p / GONE).read_bytes())
        self.assertIn(GONE, self.lock())


class DeleteFailureReportTests(RemovalBase):
    """sync delete: the report must reflect what really happened after each partial failure."""
    def modified_deep(self):
        self.drop_source(DEEP)
        (self.p / DEEP).write_bytes(b'my notes')
        return self.status()['removals']['decisions'][0]

    def call_sync(self, ps, item, decision='delete'):
        return ps.sync(str(self.p), decision, DEEP, item['source_hash'] or 'removed', item['local_hash'])

    def test_rmdir_failure_after_successful_unlink_reports_the_deletion(self):
        item = self.modified_deep()
        ps = load_module(self.box.helper, 'delete_rmdir')
        with mock.patch.object(ps.os, 'rmdir', side_effect=OSError(16, 'Device busy')):
            data = self.call_sync(ps, item)
        self.assertFalse(data['ok'])
        self.assertEqual(([DEEP], True, False, 'stop'), (data['removed']['files'], data['changed']['file'],
                                                         data['changed']['lock'], data['next']))
        self.assertFalse((self.p / DEEP).exists())
        self.assertIn(DEEP, self.lock())  # lock not written yet: the next status heals it
        self.assertEqual(([DEEP], 'skeleton'), (self.status()['removals']['lock_cleanup'], self.status()['next']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertNotIn(DEEP, self.lock())
        self.assertEqual('ready', self.status()['next'])

    def test_lock_write_failure_after_successful_delete_reports_partial_change_and_resumes(self):
        item = self.modified_deep()
        ps = load_module(self.box.helper, 'delete_lock')
        with mock.patch.object(ps, 'write_lock', side_effect=OSError('disk full')):
            data = self.call_sync(ps, item)
        self.assertFalse(data['ok'])
        self.assertEqual(([DEEP], True, False), (data['removed']['files'], data['changed']['file'], data['changed']['lock']))
        self.assertFalse((self.p / DEEP).exists())
        self.assertIn(DEEP, self.lock())
        status = self.status()
        self.assertEqual(([DEEP], 'skeleton'), (status['removals']['lock_cleanup'], status['next']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(('ready', False), (self.status()['next'], DEEP in self.lock()))

    def test_failure_before_unlink_reports_no_change(self):
        item = self.modified_deep()
        ps = load_module(self.box.helper, 'delete_unlink')
        with mock.patch.object(ps.os, 'unlink', side_effect=OSError(1, 'Operation not permitted')):
            data = self.call_sync(ps, item)
        self.assertEqual((False, False, [], b'my notes'), (data['ok'], data['changed']['file'], data['removed']['files'],
                                                         (self.p / DEEP).read_bytes()))


class GeneratorCooperationTests(WorkflowFixture, unittest.TestCase):
    """Generator integration: the real generator and real templates are the subject, not the removal rules."""
    def test_skeleton_after_generator_and_evidence_leaves_active_files_untouched(self):
        ps = load_module(fx.SHARED / 'scripts/project_setup.py', 'removal_flow')
        self.assertTrue(ps.language_only(str(self.plugin), 'de')['ok'])
        self.create()  # existing generator (R17: configuration first); it already writes the common files it owns
        active = fx.FILES[0]
        written = (self.plugin / active).read_bytes()
        self.assertTrue(ps.record(str(self.plugin), 'plugin', 'new-plugin')['ok'])
        self.assertEqual(('plugin', 'skeleton'), (ps.status(str(self.plugin))['state'], ps.status(str(self.plugin))['next']))
        self.assertTrue(ps.setup(str(self.plugin))['ok'])  # records evidence for identical files, removes nothing active
        status = ps.status(str(self.plugin))
        self.assertEqual(('plugin', 'ready'), (status['state'], status['next']))
        self.assertEqual(written, (self.plugin / active).read_bytes())
        self.assertEqual(fx.template(active), (self.plugin / active).read_bytes())
