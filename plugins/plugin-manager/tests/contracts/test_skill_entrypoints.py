"""Public skill inventory and shared resources must survive host distribution."""
import json
from pathlib import Path
import re
import tempfile
import unittest

from tests.support.plugin_fixture import materialize

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
NAMES = {'plugin-manager', 'marketplace-create', 'plugin-create', 'configure', 'verify', 'update', 'publish'}


class SkillEntrypointTests(unittest.TestCase):
    def check_inventory(self, root):
        entries = list((root/'skills').glob('*/SKILL.md'))
        self.assertEqual(NAMES, {p.parent.name for p in entries})
        for path in entries:
            text = path.read_text()
            self.assertEqual(path.parent.name, re.search(r'^name: (.+)$', text, re.M)[1])
            self.assertIn('../_shared/WORKFLOWS.md', text)
            for relative in re.findall(r'`(\.\./_shared/[^`]+)`', text):
                self.assertTrue((path.parent/relative.split(' ', 1)[0]).is_file(), relative)
        self.assertFalse((root/'skills/_shared/SKILL.md').exists())
        for relative in ('WORKFLOWS.md', 'references/publish.md', 'references/prerequisites.md',
                         'scripts/publish_plan.py', 'scripts/workflows.py', 'scripts/verify.py',
                         'scripts/documentation.py', 'templates/plugin/Makefile', 'templates/marketplace/Makefile'):
            self.assertTrue((root/'skills/_shared'/relative).is_file(), relative)

    def test_source_has_exactly_six_public_skills(self):
        self.check_inventory(ROOT)
        manifest = json.loads((ROOT/'plugin.json').read_text())
        self.assertEqual('./skills/verify/SKILL.md', manifest['extensions']['com.openai']['onboardingSkill'])
        config = json.loads((ROOT/'docs/documentation.json').read_text())
        self.assertTrue((ROOT/config['source_skill']/'SKILL.md').is_file())
        self.assertIn('skills/_shared/WORKFLOWS.md', config['extra_sources'])

    def test_both_host_payloads_keep_shared_rules_and_six_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            for host in ('claude', 'codex'):
                with self.subTest(host=host):
                    self.check_inventory(materialize(Path(directory)/host, host))

    def test_claude_commands_route_to_public_skills_and_explicit_variants(self):
        for name in NAMES:
            self.assertIn(f'/skills/{name}/SKILL.md', (ROOT/'commands'/f'{name}.md').read_text())
        for name, kind in [('plugin-verify', 'plugin'), ('marketplace-verify', 'marketplace')]:
            text = (ROOT/'commands'/f'{name}.md').read_text()
            self.assertIn('skills/verify/SKILL.md', text)
            self.assertIn('--kind '+kind, text)
        self.assertFalse((ROOT/'commands/init.md').exists())
