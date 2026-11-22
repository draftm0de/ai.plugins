"""Sync rules of the skeleton (lock v2 hash pairs, keep/adopt) on a minimal FICTIONAL parent.

The real project_setup.py and the real operator_language.py run unchanged; only the managed list of the copied
script is replaced by a fixed fictional list whose bytes are defined in the fixture. Expectations come from those
literals and from hashlib, never from the production templates. The class at the end is the separate
generator integration test with the real generator and real templates."""
import json
import os
import shutil
import stat
import unittest
from unittest import mock

from tests.support.workflow_fixture import WorkflowFixture  # puts the Manager scripts on sys.path
from tests.integration.project_setup.test_setup import load_module
from tests.support import project_setup_fixture as fx
from tests.support.project_setup_fixture import (ALPHA, BETA, DELTA, FICTIONAL, GAMMA, LOCK, ZETA, FictionalSandbox,
                                                 digest, tree)

TARGET = 'alpha.md'  # a fictional managed file
NESTED = 'tools/deep/gamma.sh'


def entry(source, local=None):
    """Expected lock entry, hashed here from literal bytes (independent of the helper)."""
    return {'source_hash': digest(source), 'local_hash': digest(source if local is None else local)}


EXPECTED_LOCK = {path: entry(data) for path, (data, _) in FICTIONAL.items()}


class SyncBase(unittest.TestCase):
    def setUp(self):
        self.box = FictionalSandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project  # plugin.json present: state plugin

    def setup_all(self, language='de'):
        self.assertEqual(0, self.box.call('language', '--language', language)[0])
        code, data, _ = self.box.call('setup')
        self.assertEqual((0, True), (code, data['ok']))

    def status(self):
        code, data, _ = self.box.call('status')
        self.assertEqual(0, code, data)
        return data

    def decide(self, decision, path=TARGET, expect_ok=True, item=None):
        item = item or next(d for d in self.status()['sync']['decisions'] if d['path'] == path)
        code, data, result = self.box.call('sync', '--decision', decision, '--path', path,
                                           '--source-hash', item['source_hash'], '--local-hash', item['local_hash'])
        self.assertEqual(expect_ok, data['ok'] and code == 0, (data, result.stderr))
        return data

    def lock(self):
        return json.loads((self.p / LOCK).read_text())

    def deviate(self, content=b'my version'):
        (self.p / TARGET).write_bytes(content)


class CopyAndIdempotenceTests(SyncBase):
    def test_missing_files_are_copied_with_nested_parents_modes_and_both_hashes(self):
        self.setup_all()
        for path, (data, executable) in FICTIONAL.items():
            self.assertEqual(data, (self.p / path).read_bytes(), path)
            self.assertEqual(executable, bool((self.p / path).stat().st_mode & 0o111), path)
        for folder in ('docs', 'tools', 'tools/deep'):
            self.assertTrue((self.p / folder).is_dir())
        self.assertEqual({'schema_version': 2, 'files': EXPECTED_LOCK}, self.lock())

    def test_repeat_writes_nothing_and_asks_nothing(self):
        self.setup_all()
        before = tree(self.p)
        for _ in range(2):
            code, data, _ = self.box.call('setup')
            self.assertEqual((0, [], False), (code, data['created']['files'], data['lock']['changed']))
        self.assertEqual(before, tree(self.p))
        status = self.status()
        self.assertEqual(('ready', True, False), (status['next'], status['matches_template'], status['sync']['needed']))

    def test_identical_file_gets_missing_or_stale_pair_without_dialog_and_keeps_its_mode(self):
        self.setup_all()
        (self.p / TARGET).chmod(0o600)
        data = self.lock()
        data['files'][TARGET] = {'source_hash': '0' * 64, 'local_hash': '0' * 64}
        del data['files']['delta.md']
        (self.p / LOCK).write_text(json.dumps(data))
        status = self.status()
        self.assertEqual(('skeleton', False), (status['next'], status['sync']['needed']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(EXPECTED_LOCK, self.lock()['files'])
        self.assertEqual(0o600, stat.S_IMODE((self.p / TARGET).stat().st_mode))

    def test_locally_missing_file_is_recreated_even_with_a_lock_entry(self):
        self.setup_all()
        (self.p / 'docs/beta.txt').unlink()
        self.assertEqual('skeleton', self.status()['next'])
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(BETA, (self.p / 'docs/beta.txt').read_bytes())

    def test_deviation_without_lock_needs_a_decision_and_is_not_accepted(self):
        self.setup_all()
        (self.p / LOCK).unlink()
        self.deviate()
        status = self.status()
        item = status['sync']['decisions'][0]
        self.assertEqual(('no_accepted_pair', TARGET, None), (item['reason'], item['path'], item['accepted']))
        self.assertEqual(('skeleton', 'decision_needed'), (status['next'], status['files'][TARGET]))  # identical files first
        self.box.call('setup')  # a skeleton run keeps the undecided deviation untouched
        self.assertEqual('sync', self.status()['next'])
        self.assertEqual(b'my version', (self.p / TARGET).read_bytes())
        self.assertNotIn(TARGET, self.lock()['files'])

    def test_only_deviating_files_create_no_lock_and_no_ownership(self):
        for path in FICTIONAL:
            target = self.p / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b'x')
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        data = self.box.call('setup')[1]
        self.assertEqual((sorted(FICTIONAL), False), (data['different'], (self.p / LOCK).exists()))
        self.assertEqual(len(FICTIONAL), len(self.status()['sync']['decisions']))

    def test_status_with_open_decisions_writes_and_asks_nothing(self):
        self.setup_all(); self.deviate()
        before, manager = tree(self.p), tree(self.box.manager)
        data = self.status()
        self.assertTrue(data['sync']['needed'])
        self.assertEqual((before, manager), (tree(self.p), tree(self.box.manager)))
        item = data['sync']['decisions'][0]
        for key in ('path', 'reason', 'source_hash', 'local_hash', 'accepted', 'source_changed', 'local_changed', 'source_file', 'local_file'):
            self.assertIn(key, item)
        self.assertEqual((digest(ALPHA), digest(b'my version')), (item['source_hash'], item['local_hash']))

    def test_additional_local_files_and_folders_are_never_deleted(self):
        extras = {'docs/own.md': b'x', 'tools/own_tool.py': b'y', 'mine/SKILL.md': b'z', 'notes/todo.txt': b'n'}
        for name, data in extras.items():
            path = self.p / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        self.setup_all(); self.deviate(); self.decide('adopt')
        for name, data in extras.items():
            self.assertEqual(data, (self.p / name).read_bytes())

    def test_unmanaged_agents_file_is_not_touched_or_locked(self):
        (self.p / 'AGENTS.md').write_text('mine')
        self.setup_all()
        self.assertEqual('mine', (self.p / 'AGENTS.md').read_text())
        self.assertNotIn('AGENTS.md', self.lock()['files'])


class DecisionTests(SyncBase):
    def test_keep_preserves_bytes_records_both_current_hashes_and_stops_asking(self):
        self.setup_all(); self.deviate()
        data = self.decide('keep')
        self.assertEqual((True, False, 'status'), (data['changed']['lock'], data['changed']['file'], data['next']))
        self.assertEqual(b'my version', (self.p / TARGET).read_bytes())
        self.assertEqual(entry(ALPHA, b'my version'), self.lock()['files'][TARGET])
        status = self.status()
        self.assertEqual(('ready', False, [TARGET], False), (status['next'], status['sync']['needed'],
                                                            status['skeleton']['accepted_deviations'], status['matches_template']))
        before = tree(self.p)
        for _ in range(2):  # repetition: no dialog, no writes
            self.box.call('setup'); self.status()
        self.assertEqual(before, tree(self.p))

    def test_source_change_asks_again_and_adopt_replaces_and_records_template_pair(self):
        self.setup_all(); self.deviate(); self.decide('keep')
        new = ALPHA + b'# new template line\n'
        self.box.set_template(TARGET, new)
        item = self.status()['sync']['decisions'][0]
        self.assertEqual(('source_changed', True, False), (item['reason'], item['source_changed'], item['local_changed']))
        (self.p / TARGET).chmod(0o640)
        data = self.decide('adopt')
        self.assertEqual((True, True), (data['changed']['file'], data['changed']['lock']))
        self.assertEqual(new, (self.p / TARGET).read_bytes())
        self.assertEqual(0o640, stat.S_IMODE((self.p / TARGET).stat().st_mode))  # existing mode is kept
        self.assertEqual(entry(new), self.lock()['files'][TARGET])
        self.assertEqual('ready', self.status()['next'])

    def test_local_change_asks_again(self):
        self.setup_all(); self.deviate(); self.decide('keep')
        self.deviate(b'my version, edited again')
        item = self.status()['sync']['decisions'][0]
        self.assertEqual(('local_changed', False, True), (item['reason'], item['source_changed'], item['local_changed']))
        self.decide('keep')
        self.assertEqual(entry(ALPHA, b'my version, edited again'), self.lock()['files'][TARGET])

    def test_both_changed_asks_again(self):
        self.setup_all(); self.deviate(); self.decide('keep')
        self.box.set_template(TARGET, ALPHA + b'# new\n')
        self.deviate(b'local edit')
        self.assertEqual('both_changed', self.status()['sync']['decisions'][0]['reason'])

    def test_adopt_without_lock_and_local_equal_to_new_source_needs_no_dialog(self):
        self.setup_all(); (self.p / LOCK).unlink(); self.deviate()
        self.decide('adopt')
        self.assertEqual(ALPHA, (self.p / TARGET).read_bytes())
        self.assertEqual(entry(ALPHA), self.lock()['files'][TARGET])
        self.box.set_template(TARGET, b'newer source')  # local file equals a changed source: pair corrected silently
        (self.p / TARGET).write_bytes(b'newer source')
        status = self.status()
        self.assertEqual(('skeleton', False), (status['next'], status['sync']['needed']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(entry(b'newer source'), self.lock()['files'][TARGET])

    def test_only_one_file_per_decision_and_other_deviations_stay_open(self):
        self.setup_all(); self.deviate(); (self.p / 'delta.md').write_bytes(b'other deviation')
        self.assertEqual(2, len(self.status()['sync']['decisions']))
        self.decide('keep', TARGET)
        self.assertEqual(['delta.md'], [d['path'] for d in self.status()['sync']['decisions']])


class StaleAndErrorTests(SyncBase):
    def test_decision_for_another_pair_stops_without_writes(self):
        self.setup_all(); self.deviate()
        shown = self.status()['sync']['decisions'][0]
        self.deviate(b'changed after the question was shown')
        before = tree(self.p)
        code, data, _ = self.box.call('sync', '--decision', 'adopt', '--path', TARGET,
                                      '--source-hash', shown['source_hash'], '--local-hash', shown['local_hash'])
        self.assertEqual((1, 'stale_decision', 'stop'), (code, data['conflicts'][0]['code'], data['next']))
        self.assertEqual(before, tree(self.p))

    def test_no_open_decision_unknown_path_and_bad_hash_are_rejected(self):
        self.setup_all()
        before = tree(self.p)
        h = digest(ALPHA)
        for path, source, local, code in ((TARGET, h, h, 'no_decision'), ('README.md', h, h, 'unknown_path'), (TARGET, 'x', h, 'invalid_hash')):
            c, data, _ = self.box.call('sync', '--decision', 'adopt', '--path', path, '--source-hash', source, '--local-hash', local)
            self.assertEqual((1, code), (c, data['conflicts'][0]['code']))
            self.assertEqual(before, tree(self.p))
        self.deviate(); self.decide('keep')
        c, data, _ = self.box.call('sync', '--decision', 'adopt', '--path', TARGET, '--source-hash', h, '--local-hash', digest(b'my version'))
        self.assertEqual('no_decision', data['conflicts'][0]['code'])  # accepted deviation: nothing to decide
        self.assertEqual(b'my version', (self.p / TARGET).read_bytes())

    def test_old_or_damaged_lock_is_rejected_unchanged_for_every_operation(self):
        self.setup_all(); self.deviate()
        shown = self.status()['sync']['decisions'][0]
        for text in ('{"schema_version": 1, "files": {"%s": "%s"}}' % (TARGET, 'a' * 64), '{broken',
                     '{"schema_version": 2, "files": {"%s": {"source_hash": "x", "local_hash": "y"}}}' % TARGET):
            (self.p / LOCK).write_text(text)
            before = tree(self.p)
            for args in (('status',), ('setup',), ('sync', '--decision', 'adopt', '--path', TARGET,
                                                  '--source-hash', shown['source_hash'], '--local-hash', shown['local_hash'])):
                code, data, _ = self.box.call(*args)
                self.assertEqual((1, 'stop'), (code, data['next']), (text, args))
                self.assertEqual(before, tree(self.p))
        (self.p / LOCK).write_text('{"schema_version": 1, "files": {}}')
        conflict = self.box.call('status')[1]['conflicts'][0]
        self.assertEqual('lock_format', conflict['code'])
        self.assertIn('no migration', conflict['reason'])

    def test_symlink_target_is_a_conflict_before_adopt(self):
        self.setup_all(); self.deviate()
        shown = self.status()['sync']['decisions'][0]
        outside = self.box.base / 'outside.md'; outside.write_bytes(b'x')
        (self.p / TARGET).unlink(); (self.p / TARGET).symlink_to(outside)
        c, data, _ = self.box.call('sync', '--decision', 'adopt', '--path', TARGET,
                                   '--source-hash', shown['source_hash'], '--local-hash', shown['local_hash'])
        self.assertEqual(1, c)
        self.assertEqual(b'x', outside.read_bytes())

    def test_lock_write_failure_after_adopt_reports_actual_partial_change(self):
        self.setup_all(); self.deviate()
        ps = load_module(self.box.helper, 'sync_partial')
        item = self.status()['sync']['decisions'][0]
        with mock.patch.object(ps, 'write_lock', side_effect=OSError('disk full')):
            data = ps.sync(str(self.p), 'adopt', TARGET, item['source_hash'], item['local_hash'])
        self.assertEqual((False, True, False, 'stop'), (data['ok'], data['changed']['file'], data['changed']['lock'], data['next']))
        self.assertEqual(ALPHA, (self.p / TARGET).read_bytes())
        self.assertEqual(entry(ALPHA), self.lock()['files'][TARGET])  # lock untouched by the failed write
        self.assertEqual('ready', self.status()['next'])  # the file is identical again and its earlier pair still fits


class ReportShapeTests(SyncBase):
    def test_setup_reports_target_state_not_file_state_and_refuses_unconfigured_targets(self):
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        code, data, _ = self.box.call('setup')  # configured by evidence
        self.assertEqual((0, 'plugin', True, 'demo-plugin'), (code, data['state'], data['plugin_configured'], data['plugin']))
        self.box.unconfigure()  # same folder, now without configuration evidence: no skeleton exists (R17)
        (self.p / 'plugin.json').write_text('{"name": "demo-plugin"}')  # product only, never evidence
        (self.p / 'delta.md').write_bytes(b'mine')  # a deviation must not leak its file state either
        for operation in ('setup', 'sync'):
            before = tree(self.p)
            args = ('--decision', 'keep', '--path', 'delta.md', '--source-hash', 'a' * 64, '--local-hash', 'b' * 64) if operation == 'sync' else ()
            code, data, _ = self.box.call(operation, *args)
            self.assertEqual((1, False, 'stop', 'not_configured'), (code, data['ok'], data['next'], data['conflicts'][0]['code']), operation)
            self.assertIn('Configure first', data['conflicts'][0]['reason'])
            self.assertEqual(before, tree(self.p), operation)
        status = self.status()
        self.assertEqual(('unconfigured', False, False, [], False), (status['state'], status['plugin_configured'], status['matches_template'],
                                                                      status['missing']['files'], status['skeleton']['open']))

    def test_sync_reports_no_new_folder_for_a_configured_workpackage(self):
        # Evidence lives in the management folder, so a configured workpackage always has it: nothing is reported as created.
        (self.p / TARGET).write_bytes(b'my version')  # deviating file
        item = next(d for d in self.status()['sync']['decisions'] if d['path'] == TARGET)
        code, data, _ = self.box.call('sync', '--decision', 'keep', '--path', TARGET,
                                      '--source-hash', item['source_hash'], '--local-hash', item['local_hash'])
        self.assertEqual((0, True, []), (code, data['ok'], data['created']['directories']))
        self.assertEqual(entry(ALPHA, b'my version'), self.lock()['files'][TARGET])
        self.assertEqual(b'my version', (self.p / TARGET).read_bytes())


class RoutingTests(SyncBase):
    def test_priority_language_then_configure_then_skeleton_then_sync_then_ready(self):
        self.box.unconfigure()
        (self.p / 'plugin.json').write_text('{"name": "demo-plugin"}')  # the generator's product; still no evidence
        (self.p / TARGET).write_bytes(b'mine')
        self.assertEqual('language', self.status()['next'])
        self.box.call('language', '--language', 'de')
        self.assertEqual('configure', self.status()['next'])  # R17: configuration outranks skeleton and sync
        self.box.configure()
        self.assertEqual('skeleton', self.status()['next'])  # missing files first
        self.box.call('setup')
        self.assertEqual('sync', self.status()['next'])
        self.decide('keep')
        self.assertEqual('ready', self.status()['next'])

    def test_full_sequence_without_git_or_origin_then_ready_with_evidence(self):
        self.box.unconfigure()
        self.assertEqual('language', self.status()['next'])
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        self.assertEqual('configure', self.status()['next'])
        self.assertEqual(1, self.box.call('setup')[0])  # no skeleton before the kind is known
        status = self.status()
        self.assertEqual(('configure', False, False), (status['next'], status['plugin_configured'], status['skeleton']['open']))
        self.assertFalse((self.p / LOCK).exists() or (self.p / 'plugin.json').exists() or (self.p / '.git').exists())
        (self.p / 'plugin.json').write_text('{"name": "demo-plugin"}')
        self.assertEqual('configure', self.status()['next'])  # a root plugin.json is a product, never evidence
        self.box.configure()
        self.assertEqual('skeleton', self.status()['next'])
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual(EXPECTED_LOCK, self.lock()['files'])
        self.assertEqual('ready', self.status()['next'])

    def test_resume_after_missing_lock_or_file(self):
        (self.p / '.git').mkdir(); (self.p / '.git/HEAD').write_text('ref: refs/heads/main\n')
        self.setup_all()
        (self.p / LOCK).unlink()
        data = self.status()
        self.assertEqual(('skeleton', sorted(FICTIONAL)), (data['next'], sorted(data['skeleton']['lock_pending'])))
        self.assertEqual(0, self.box.call('setup')[0])
        (self.p / 'delta.md').unlink()
        self.assertEqual(('skeleton', ['delta.md']), (self.status()['next'], self.status()['skeleton']['missing_files']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual('ready', self.status()['next'])
        self.assertEqual('ref: refs/heads/main\n', (self.p / '.git/HEAD').read_text())

    def test_stored_language_with_missing_ignore_rule_routes_to_skeleton(self):
        (self.p / '.project').mkdir(exist_ok=True)
        (self.p / '.project/operator.json').write_text('{"schema_version": 1, "operator_language": "de"}')
        (self.p / '.gitignore').write_text('build/\n')
        data = self.status()
        self.assertEqual(('skeleton', True), (data['next'], data['skeleton']['ignore_rule_pending']))
        self.assertEqual(0, self.box.call('setup')[0])
        self.assertEqual('build/\n/.project/operator.json\n', (self.p / '.gitignore').read_text())

    def test_existing_plugin_deviation_is_ready_after_a_keep_decision_but_never_matches(self):
        self.setup_all()
        (self.p / 'delta.md').write_bytes(b'edited')
        self.assertEqual(('sync', ['delta.md']), (self.status()['next'], self.status()['skeleton']['different']))
        self.decide('keep', 'delta.md')
        data = self.status()
        self.assertEqual(('ready', False), (data['next'], data['matches_template']))  # ready is not template equality


REAL_TARGET = 'scripts/plugin.py'  # real skeleton file used only by the generator integration test


class GeneratorCooperationTests(WorkflowFixture, unittest.TestCase):
    """Generator integration: the real generator and the real templates are the subject here, not the sync rules."""
    def setUp(self):
        super().setUp()
        self.ps = load_module(fx.SHARED / 'scripts/project_setup.py', 'sync_flow')

    def prepare(self):
        """A deviating common file exists before the generator runs (R17: the generator never judges it)."""
        (self.plugin / 'scripts').mkdir()
        (self.plugin / REAL_TARGET).write_bytes(b'my own version')

    def generate_and_record(self):
        self.create()  # existing generator: creates the product and missing files, leaves the deviating one alone
        self.assertTrue(self.ps.language_only(str(self.plugin), 'de')['ok'])
        self.assertEqual('configure', self.ps.status(str(self.plugin))['next'])
        self.assertTrue(self.ps.record(str(self.plugin), 'plugin', 'new-plugin')['ok'])

    def item(self):
        return self.ps.status(str(self.plugin))['sync']['decisions'][0]

    def test_existing_deviating_common_file_does_not_block_the_generator_and_stays_open_for_sync(self):
        self.prepare()
        market_before = tree(self.market)
        self.generate_and_record()
        self.assertEqual(b'my own version', (self.plugin / REAL_TARGET).read_bytes())  # byte-identical, not judged
        self.assertNotEqual(market_before, tree(self.market))  # the marketplace association was written
        status = self.ps.status(str(self.plugin))
        self.assertEqual(('skeleton', True, [REAL_TARGET]), (status['next'], status['sync']['needed'], status['skeleton']['different']))
        self.assertTrue(self.ps.setup(str(self.plugin))['ok'])  # skeleton evidence for the identical files only
        self.assertEqual('sync', self.ps.status(str(self.plugin))['next'])
        item = self.item()
        self.assertTrue(self.ps.sync(str(self.plugin), 'keep', REAL_TARGET, item['source_hash'], item['local_hash'])['ok'])
        self.assertEqual(b'my own version', (self.plugin / REAL_TARGET).read_bytes())
        status = self.ps.status(str(self.plugin))
        self.assertEqual(('ready', False), (status['next'], status['matches_template']))

    def test_adopted_template_after_generator_then_status_ready(self):
        self.prepare()
        self.generate_and_record()
        self.assertTrue(self.ps.setup(str(self.plugin))['ok'])
        item = self.item()
        self.assertTrue(self.ps.sync(str(self.plugin), 'adopt', REAL_TARGET, item['source_hash'], item['local_hash'])['ok'])
        status = self.ps.status(str(self.plugin))
        self.assertEqual(('ready', False), (status['next'], status['sync']['needed']))
        self.assertEqual(fx.template(REAL_TARGET), (self.plugin / REAL_TARGET).read_bytes())
        self.assertTrue(self.ps.setup(str(self.plugin))['matches_template'])
