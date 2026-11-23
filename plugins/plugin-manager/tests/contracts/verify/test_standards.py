"""R27: the standards come with every plugin, identical, and verify finds a missing, changed or copied standard."""
from pathlib import Path
import sys
import tempfile
import unittest

R = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(R / 'skills/_shared/scripts'))
import plugin_audit as audit

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
        self.assertEqual({'standards:' + n: 'pass' for n in NAMES} | {'standards:reference': 'pass', 'standards:scope': 'pass'}, self.status())
        claude = (self.plugin / 'CLAUDE.md').read_text()
        for name in NAMES:
            self.assertIn('@docs/standards/' + name, claude)

    def test_a_missing_or_changed_standard_is_a_finding(self):
        (self.plugin / 'docs/standards/coding.md').write_text('my own rules\n')
        (self.plugin / 'docs/standards/testing.md').unlink()
        found = self.status()
        self.assertEqual(('fail', 'fail'), (found['standards:coding.md'], found['standards:testing.md']))
        self.assertEqual('pass', found['standards:messages.md'])
        self.assertFalse(audit.audit(self.plugin)['structurally_valid'])

    def test_agents_md_must_point_to_the_standards(self):
        agents = self.plugin / 'AGENTS.md'
        agents.write_text(agents.read_text().split('## Standards')[0])
        self.assertEqual('fail', self.status()['standards:reference'])

    def test_a_standard_copied_into_the_scope_is_a_finding(self):
        line = next(l.strip() for l in (SOURCE / 'coding.md').read_text().splitlines() if len(l.strip()) >= 60)
        scope = self.plugin / 'SCOPE.md'
        scope.write_text(scope.read_text() + '\n' + line + '\n')
        self.assertEqual('fail', self.status()['standards:scope'])


if __name__ == '__main__':
    unittest.main()
