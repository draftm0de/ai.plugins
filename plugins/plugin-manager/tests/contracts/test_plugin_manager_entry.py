"""Skill text evidence for the central entry; documents instructions, not model/host behavior."""
from pathlib import Path
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())


class EntryTextTests(unittest.TestCase):
    def setUp(self):
        # The entry rules are the common flow plus the Manager's slim SKILL.md (R19); needles check both together.
        self.skill = (ROOT / 'skills/setup/SKILL.md').read_text()
        self.entry = (ROOT / 'skills/setup/flows/entry.md').read_text()
        self.text = self.skill + '\n' + self.entry

    def flow(self, name):
        return (ROOT / 'skills/setup/flows' / (name + '.md')).read_text()

    def test_loop_routes_by_status_and_rechecks_after_each_flow(self):
        for needle in ('status --target', '`stop`', '`language`', '`skeleton`', '`configure`', '`ready`',
                       'language.md', 'skeleton.md', '../../setup/flows/configure.md', 'flows/configure.md',
                       'After each flow that succeeded in this sense', 'run `status` again'):
            self.assertIn(needle, self.text)
        for name in ('language', 'skeleton', 'configure'):
            self.assertIn('run `status` again', self.flow(name))
        order = [self.entry.index(m) for m in ('`stop` (`state: conflict`', '| `language` |', '| `configure` |', '| `skeleton` |', '| `ready` |')]
        self.assertEqual(sorted(order), order)  # fixed priority in the routing table

    def test_stop_rules_no_endless_loops_and_ready_waits(self):
        for needle in ('Stop and report instead of repeating', 'same `next` without progress', 'do not ask again in a loop',
                       'wait for input', 'no endless re-sync', 'name each concrete reason', 'partial changes that actually happened'):
            self.assertIn(needle, self.text)
        for name in ('language', 'skeleton'):
            self.assertIn('Check `ok` and the exit code', self.flow(name))
            self.assertIn('partial changes that actually happened', self.flow(name))

    def test_read_only_precedence(self):
        for needle in ('Read-only requests', 'exactly one `status`', 'ask nothing, save nothing, start no flow'):
            self.assertIn(needle, self.text)

    def test_language_flow_asks_alone_and_saves_only_after_answer(self):
        text = self.flow('language')
        for needle in ('Ask alone', 'wait for an actual answer', 'does not', 'language --target'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Ask alone'), text.index('language --target'))

    def test_configure_flow_keeps_skeleton_and_invents_nothing(self):
        text = self.flow('configure')
        for needle in ('../../_shared/references/workflows.md', 'in this folder', 'never invent or dummy-fill', 'explicitly selected',
                       'never roll anything back', 'not a failure of the skeleton', 'nothing is replaced', 'remotes'):
            self.assertIn(needle, text)
        for rule in ('Silence is not deferral', '--license MIT', '--copyright-holder',
                     '--license-file', 'checks.licensing', 'Never execute target code',
                     'nonfunctional scaffold', 'Never offer skill import'):
            self.assertIn(rule, text)

    def test_configure_dialogue_is_guided_after_abort_like_the_first_call(self):
        text = self.flow('configure')
        for needle in ('identical on the first call, after an aborted dialogue', 're-reads `status` and this flow',
                       'Do not summarize all open facts as a text list', 'do not ask which dialogue form',
                       'explicitly answered in the current conversation', 'cancelled, dismissed, rejected by the host or left unanswered is not an answer',
                       "host's question tool", 'exactly one targeted text question per message',
                       'explicit request of the person for a complete list or a text mode',
                       'configuration is paused', 'Do not ask again on your own', 'next call of this entry continues'):
            self.assertIn(needle, text)
        self.assertIn('a cancelled or unanswered question is such a pause', self.text)
        # existing prerequisites and result rules are kept
        for needle in ('explicitly selected', 'never invent or dummy-fill', 'checks.status == "passed"', 'never roll anything back'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Guided dialogue'), text.index('Only an explicit request'))
        self.assertIn('exactly one `status`', self.text)  # read-only unchanged

    def test_marketplace_selection_tool_errors_and_generator_timing(self):
        text = self.flow('configure')
        for needle in ('suggestion is never a selection',
                       'Even with a single candidate', 'explicit confirmation of the concrete path', '"Use this checkout"',
                       '"Choose another checkout"', 'never add a filler option',
                       'because of a suggestion, a preselection or a tool error', 'ask for the path with one targeted question',
                       'already confirmed explicitly in this conversation is not asked again',
                       'schema error or rejection of a question call means that no question in it was answered',
                       'Ask the valid questions again, separately', 'duty of an explicit selection stays',
                       'after every answer and after a tool error', 'rejected by the host',
                       'one targeted text question per message', 'no configuration write before step 4',
                       'Missing choices are asked first', 'only after a deliberate postponement or cancellation',
                       'no answer can fix', 'never replaces asking for a missing selection',
                       'Run the generator only after all required facts are answered and the marketplace checkout is explicitly confirmed',
                       'Until then nothing is written for the configuration'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Run the generator only after'), text.index('Judge the result'))
        self.assertIn('no answer can fix', self.text)
        self.assertIn('first asked for in the guided dialogue', self.text)

    def test_entry_reads_common_language_rule_instead_of_duplicating_it(self):
        reference = (ROOT / 'skills/_shared/references/operator-language.md').read_text()
        self.assertIn('## Language of all visible text', reference)
        for needle in ('read and apply `../../_shared/references/operator-language.md`', 'Language of all visible text',
                       'closing or next-step card fields'):
            self.assertIn(needle, self.text)
        for duplicated in ('Apply the language before output', 'Fixed labels the host itself supplies', 'JSON keys are not translated'):
            self.assertNotIn(duplicated, self.text)
        self.assertTrue((ROOT / 'skills/setup/../_shared/references/operator-language.md').is_file())
        # manager-specific rules stay in the entry
        for needle in ('read-only asks and saves no language', 'setup order with the ignore rule', 'on `ready` output only the ready line and wait',
                       'start no verify or other action on your own', 'exactly one `status`', 'Precedence: this entry'):
            self.assertIn(needle, self.text)
        self.assertIn('flow', self.text)

    def test_sync_flow_is_dialogue_guided_explicit_and_stops_on_stale_decisions(self):
        text = self.flow('sync')
        for needle in ('Python never asks', 'one file at a time', 'in the operator language', 'Show only the file path', 'Do not show file contents',
                       'Keep local file', 'Adopt template', 'A preselection, silence, a cancelled or rejected question is not a decision',
                       'nothing is written or stored', 'sync --target', '--decision keep|adopt', '--source-hash', '--local-hash',
                       'records both current hashes', 'replaces only this file', 'Only the explicitly chosen file is touched',
                       '`stale_decision`', 'not applied', 'run `status` again', 'never mean `matches_template`',
                       'Check `ok` and the exit code', 'partial changes that actually happened'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Ask explicitly'), text.index('sync --target'))

    def test_entry_routes_sync_after_skeleton_and_keeps_replace_boundary(self):
        order = [self.entry.index(m) for m in ('| `skeleton` |', '| `sync` |', '| `ready` |')]
        self.assertEqual(sorted(order), order)
        for needle in ('sync.md', 'Deletion is limited to a managed file whose source was removed', 'only by an explicit `adopt` decision',
                       'schema_version 2', 'rejected unchanged, never migrated', '`accepted`', '`decision_needed`',
                       '`language`, `setup`, `sync` and `record`'):
            self.assertIn(needle, self.text)
        self.assertIn('Deviations are only resolved by the sync flow', self.flow('configure'))
        self.assertIn('decision is the separate sync flow', self.flow('skeleton'))

    def test_relative_references_in_skill_and_flows_resolve_to_existing_files(self):
        import re
        sources = [ROOT / 'skills/setup/SKILL.md', ] + sorted((ROOT / 'skills/setup/flows').glob('*.md'))
        checked = 0
        for source in sources:
            for reference in re.findall(r'`(\.\./[^`\s]+)`', source.read_text()):
                reference = reference.replace('<plugin>', 'plugin-manager')  # the Manager is the plugin of these checks
                if '<kind>' in reference:
                    continue  # a pattern over the manifests, not a file
                checked += 1
                self.assertTrue((source.parent / reference.split('#')[0]).exists(), str(source.name) + ': ' + reference)
        self.assertGreater(checked, 5)
        self.assertIn('`../../_shared/references/operator-language.md`', self.flow('sync'))
        self.assertNotIn('(see `../_shared/references/operator-language.md`)', self.flow('sync'))

    def test_no_outdated_never_updated_texts_contradict_the_sync(self):
        description = self.text.split('---')[1]
        self.assertNotIn('never updated', description)
        self.assertIn("replaced only by the person's explicit adopt decision", description)
        self.assertNotIn('never overwritten, no endless re-sync', self.text)
        for needle in ('never overwritten automatically', 'Only an explicit `adopt` takes over the template content',
                       '`accepted` deviation', 'neither re-asked nor reported as matching the template'):
            self.assertIn(needle, self.text)

    def test_removal_rules_and_no_content_display_are_instructed(self):
        for needle in ('stored `local_hash` and the stored `source_hash`', 'without lock evidence nothing is ever deleted',
                       'always asked (keep or delete)', 'only lose their lock entry', 'bottom-up with `rmdir`',
                       '`.git`, `.idea` or `.project`', 'foreign files are never deleted', '`removals`', '`unowned`'):
            self.assertIn(needle, self.text)
        sync = self.flow('sync')
        for needle in ('removal question', 'Delete local file', '--source-hash removed', '`source_hash: null`',
                       'does not ask again while a later local change does', 'no file content, excerpt, diff or summary is ever shown',
                       'its source was removed in the parent template'):
            self.assertIn(needle, sync)
        self.assertIn('removals.auto', self.flow('skeleton'))
        self.assertIn('Do not show file contents, text excerpts, a diff or a content summary', sync)

    def test_cli_forms_partial_reports_replace_boundary_and_no_content_summaries(self):
        sync = self.flow('sync')
        for needle in ('--decision keep|adopt --path', '--decision keep|delete --path', '--source-hash removed',
                       'for a content question', 'for a removal question'):
            self.assertIn(needle, sync)
        self.assertNotIn('keep|adopt|delete', sync)
        skeleton = self.flow('skeleton')
        self.assertIn('`removed.files`, `removed.directories`', skeleton.split('2. Check')[1].split('3.')[0])
        self.assertIn('`removed.*`', sync)
        self.assertNotIn('every other flow leave its bytes unchanged', self.text)
        for needle in ('never replace its bytes', 'only the automatic removal and the explicit `delete` decision',
                       'Never show, quote or describe the content', 'not for `ready`', 'not for accepted deviations or kept files',
                       'Name only the path and the fact'):
            self.assertIn(needle, self.text)

    def test_success_is_judged_per_flow_answer(self):
        for needle in ('exit 0 and `ok: true`', 'no `ok`', '`checks.status == "passed"`', '`needs_attention`',
                       '`changed`', 'only after that success', 'cannot be shown as `ready`'):
            self.assertIn(needle, self.text)
        text = self.flow('configure')
        for needle in ('no `ok`', 'exit 0 **and** `checks.status == "passed"`', 'needs_attention', 'files actually listed in `changed`',
                       'do not say "ready"', 'do not derive success from a plugin.json that now exists',
                       'Only after a passed run write the evidence'):
            self.assertIn(needle, text)
        self.assertLess(text.index('needs_attention'), text.index('Only after a passed run write the evidence'))

    def test_precedence_over_language_reference_and_management_file_exceptions(self):
        for needle in ('Precedence: this entry', 'do not apply here', '.gitignore', '.project/operator.json',
                       '.project/plugins/plugin-manager/skeleton.json'):
            self.assertIn(needle, self.text)

    def test_ready_is_one_status_line_in_the_operator_language(self):  # R18
        for needle in ('Plugin plugin-manager Status: fully configured', 'Plugin plugin-manager Status: vollständig konfiguriert',
                       'exactly one line', 'nothing else'):
            self.assertIn(needle, self.text)

    def test_configuration_evidence_per_plugin_and_kind_question_first(self):  # R15, R17
        for needle in ('--plugin plugin-manager', '.project/plugins/plugin-manager/config.json', 'never evidence',
                       'language, configuration, skeleton, sync, ready'):
            self.assertIn(needle, self.text)
        text = self.flow('configure')
        for needle in ('Plugin or marketplace?', 'no preselection', 'flows/marketplace.md', 'record --target', '--kind plugin|marketplace',
                       'Guided dialogue (both kinds)'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Plugin or marketplace?'), text.index('record --target'))
        self.assertNotIn('marketplace-create/SKILL.md', text)
        self.assertNotIn('lock', text.lower().replace('block', ''))  # skeleton evidence, not "lock"
        self.assertNotIn('generator refuses because a skeleton file deviates', text)

    def test_marketplace_flow_is_complete_and_self_contained(self):  # R20
        text = self.flow('marketplace')
        for needle in ('Guided dialogue (both kinds)', 'configure.md', 'create --kind marketplace --root', '--name', '--display-name', '--owner',
                       'record --target', '--kind marketplace', '--artifact', 'never taken from the Git author', 'a suggestion is never a selection',
                       'no `ok`', 'exit 0', 'idempotent', 'marketplace.json', 'local-marketplace.example.json', 'derived host catalogs',
                       'plugin repository', 'status', 'published'):
            self.assertIn(needle, text)
        self.assertLess(text.index('create --kind marketplace --root'), text.index('record --target'))
        self.assertNotIn('marketplace-create/SKILL.md', text)
        self.assertNotIn('skill `marketplace-create`', text)
        for gone in ('make verify', 'make check-marketplace'):
            self.assertNotIn(gone, text)

    def test_flows_and_references_name_the_uniform_generator_operations(self):  # R22
        paths = ('skills/setup/SKILL.md', 'skills/setup/flows/configure.md', 'skills/setup/flows/marketplace.md',
                 'skills/setup/flows/associate.md', 'skills/_shared/WORKFLOWS.md', 'skills/_shared/references/workflows.md')
        for path in paths:
            text = (ROOT / path).read_text(encoding='utf-8')
            with self.subTest(path=path):
                for old in ('plugin-create', 'marketplace-create'):
                    self.assertNotIn(old, text)
        self.assertIn('create --kind marketplace', (ROOT / 'skills/setup/flows/marketplace.md').read_text(encoding='utf-8'))
        self.assertIn('create --kind plugin', (ROOT / 'skills/setup/flows/configure.md').read_text(encoding='utf-8'))
        self.assertIn('create --kind marketplace|plugin', (ROOT / 'skills/_shared/references/workflows.md').read_text(encoding='utf-8'))

    def test_marketplace_create_skill_and_command_are_gone(self):  # R20
        self.assertFalse((ROOT / 'skills/marketplace-create').exists())
        self.assertFalse((ROOT / 'commands/marketplace-create.md').exists())
        for path in ('skills/_shared/WORKFLOWS.md', 'skills/_shared/references/workflows.md', 'skills/setup/SKILL.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertNotIn('marketplace-create/SKILL.md', text, path)
            self.assertNotIn('/plugin-manager:marketplace-create', text, path)

    def test_associate_flow_is_complete_and_self_contained(self):  # R21
        text = self.flow('associate')
        for needle in ('A plugin belongs to exactly one marketplace', 'config.json', 'local.json', 'status', '`association`',
                       'path_missing', 'path_invalid', 'mismatch', 'unsupported', 'a suggestion is never a selection',
                       'Use this checkout', 'Choose another checkout', 'Guided dialogue (both kinds)',
                       'workflows.py" associate --root', '--plugin plugin-manager', '--marketplace', '--drop-missing-old',
                       'old_catalog_entry_remains', '`action: "associate"`', 'success means exit 0', 'no `ok`',
                       'unversioned', 'publish', 'one transaction with rollback', 'never read or migrate the former plugin-side'):
            self.assertIn(needle, text)
        self.assertLess(text.index('Run `status`'), text.index('Ask for the local path'))
        self.assertLess(text.index('Ask for the local path'), text.index('workflows.py" associate --root'))
        self.assertLess(text.index('Judge the result'), text.index('Only after the person'))  # --drop-missing-old needs explicit consent
        for forbidden in ('skills/configure', 'skill `configure`', '/plugin-manager:configure', 'marketplaces` list is read'):
            self.assertNotIn(forbidden, text)

    def test_entry_routes_the_association_request_and_reports_it_only_as_a_hint(self):  # R21
        for needle in ('flows/associate.md', 'exactly one marketplace', '`association`', 'never as a gate for `ready`',
                       'local.json', 'schema_version 2', 'mandatory `marketplace` identity', 'set, change or move the marketplace'):
            self.assertIn(needle, self.text)
        self.assertNotIn('skills/configure', self.text)
        for path in ('README.md', 'README.en.md', 'docs/de/usage.md', 'docs/en/usage.md', 'skills/_shared/WORKFLOWS.md',
                     'skills/_shared/templates/package/README.md', 'skills/_shared/templates/package/README.en.md'):
            text = (ROOT / path).read_text()
            self.assertNotIn('skills/configure/SKILL.md', text, path)
            self.assertNotIn('/plugin-manager:configure', text, path)

    def test_boundaries_and_no_host_claim(self):
        for needle in ('Never the installed Manager', 'Never the installed plugin directory', 'marketplace', 'untested', 'installs nothing',
                       'never open `.git` or `.idea`', 'documented prerequisites', 'reads Git metadata',
                       'adds no Git mutation or network action', 'contains no plugin.json or placeholder identity'):
            self.assertIn(needle, self.text)
        self.assertNotIn('Git operations by this entry', self.text)

    def test_command_wrapper_routes_to_entry_skill(self):
        text = (ROOT / 'commands/setup.md').read_text()
        self.assertIn('${CLAUDE_PLUGIN_ROOT}/skills/setup/SKILL.md', text)
        self.assertIn('never the installed plugin directory', text)

    def test_command_wrapper_and_specialist_skills_unchanged(self):
        self.assertIn('/skills/setup/SKILL.md', (ROOT / 'commands/setup.md').read_text())
        # R23: docs and publish use the read-only gate, verify the read-only status; none of them calls a writing operation
        for name in ('docs', 'verify', 'publish'):
            skill = (ROOT / 'skills' / name / 'SKILL.md').read_text()
            for writer in ('setup_state.py" setup', 'setup_state.py" record', 'setup_state.py" sync', 'setup_state.py" language'):
                self.assertNotIn(writer, skill)
        self.assertNotIn('setup_state', (ROOT / 'skills/_shared/templates/plugin/seed/Makefile').read_text())
        # R23: the helper exists only in the Manager; no template ships it to generated plugins
        shipped = sorted(str(p.relative_to(ROOT / 'skills/_shared/templates')) for p in (ROOT / 'skills/_shared/templates').rglob('*')
                         if 'setup_state' in p.name)
        self.assertEqual([], shipped)
