"""R23: the Manager has exactly the public skills setup, docs, verify and publish; the call selects the instructions."""
from pathlib import Path
import re
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
SKILLS = {'setup', 'docs', 'modify', 'verify', 'publish'}
REMOVED_SKILLS = ('plugin-manager', 'update')
REMOVED_COMMANDS = ('plugin-manager', 'update', 'plugin-verify', 'marketplace-verify')
GATED = ('docs', 'modify', 'publish')  # stop with a pointer to setup when `next` is not ready


def text(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


class SkillSetTests(unittest.TestCase):
    def test_exactly_five_public_skills_each_named_like_its_folder(self):
        entries = sorted((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(SKILLS, {p.parent.name for p in entries})
        for path in entries:
            self.assertEqual(path.parent.name, re.search(r'^name: (.+)$', path.read_text(), re.M)[1])
        self.assertFalse((ROOT / 'skills/_shared/SKILL.md').exists())

    def test_former_skills_and_commands_do_not_exist_and_have_no_alias(self):
        for name in REMOVED_SKILLS:
            self.assertFalse((ROOT / 'skills' / name).exists(), name)
        for name in REMOVED_COMMANDS:
            self.assertFalse((ROOT / 'commands' / (name + '.md')).exists(), name)

    def test_every_skill_has_one_command_that_routes_to_it(self):
        self.assertEqual({name + '.md' for name in SKILLS}, {p.name for p in (ROOT / 'commands').glob('*.md')})
        for name in SKILLS:
            self.assertIn('${CLAUDE_PLUGIN_ROOT}/skills/%s/SKILL.md' % name, text('commands/%s.md' % name))
            self.assertIn('never the installed plugin directory', text('commands/%s.md' % name))

    def test_the_kind_is_never_a_call_argument(self):
        for name in ('setup', 'docs', 'modify', 'publish'):
            head = text('commands/%s.md' % name).split('---')[1]
            self.assertNotIn('kind', head.lower(), name)
        verify = text('skills/verify/SKILL.md')
        self.assertIn('--kind auto', verify)
        self.assertIn('--kind', verify.replace('--kind auto', ''))  # explicit --kind stays possible

    def test_skills_reference_only_existing_shared_files(self):
        for path in (ROOT / 'skills').glob('*/SKILL.md'):
            for relative in re.findall(r'`(\.\./_shared/[^`\s]+)', path.read_text()):
                self.assertTrue((path.parent / relative).exists(), '%s: %s' % (path.parent.name, relative))

    def test_gated_skills_check_status_and_point_to_setup(self):
        for name in GATED:
            skill = text('skills/%s/SKILL.md' % name)
            with self.subTest(skill=name):
                self.assertIn('gate', skill)
                self.assertIn('/plugin-manager:setup', skill)
                self.assertIn('writes nothing', skill)
        self.assertTrue((ROOT / 'skills/_shared/flows/gate.md').is_file())
        gate = text('skills/_shared/flows/gate.md')
        for needle in ('setup_state.py', 'gate --target', '`ready`', '/plugin-manager:setup', 'writes nothing', 'in English', 'never guess a language', '--action', 'Die Aktion', 'because', 'weil', 'Please run', 'Führe zuerst', 'Yes, run it', 'No, stop', 'Ja, ausführen', 'hand over to the skill `setup`'):
            self.assertIn(needle, gate)

    def test_verify_stays_read_only_and_reports_pending_setup_as_finding(self):
        verify = text('skills/verify/SKILL.md')
        for needle in ('read-only', 'No repairs, code execution or tests during verify', 'finding'):
            self.assertIn(needle, verify)
        for writer in ('workflows.py', 'publish_plan.py', 'setup_state.py" setup', ' record ', ' sync --'):
            self.assertNotIn(writer, verify)

    def test_only_setup_writes_configuration_skeleton_and_sync(self):
        for name in ('docs', 'modify', 'verify', 'publish'):
            skill = text('skills/%s/SKILL.md' % name)
            for writer in ('setup_state.py" setup', 'setup_state.py" record', 'setup_state.py" sync'):
                self.assertNotIn(writer, skill, name)
        self.assertTrue((ROOT / 'skills/setup/flows').is_dir())
        for name in ('configure', 'marketplace', 'associate'):
            self.assertTrue((ROOT / 'skills/setup/flows' / (name + '.md')).is_file(), name)

    def test_every_skill_and_failure_flow_follows_the_plain_message_rules(self):  # R25
        rules = text('skills/_shared/references/messages.md')
        for needle in ('Mandatory structure', 'because', 'Please', 'Führe', 'No labels', 'raw error text', 'git init', 'git remote add origin', 'Known causes', 'Unknown causes', 'Never invent a cause', 'Technische Details anzeigen', '## Address', 'German uses "du"'):
            self.assertIn(needle, rules)
        for name in SKILLS:
            self.assertIn('../_shared/references/messages.md', text('skills/%s/SKILL.md' % name), name)
        for flow in ('language', 'skeleton', 'sync', 'configure', 'marketplace', 'associate', 'entry'):
            self.assertIn('_shared/references/messages.md', text('skills/setup/flows/%s.md' % flow), flow)
        self.assertIn('messages.md', text('skills/_shared/flows/gate.md'))

    def test_setup_description_says_it_may_be_called_repeatedly(self):
        description = text('skills/setup/SKILL.md').split('---')[1]
        self.assertIn('repeatedly', description)


if __name__ == '__main__':
    unittest.main()
