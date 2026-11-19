import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

R = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(R / 'skills/_shared/scripts'))
import plugin_audit as audit
from tests.support.marketplace_fixture import attach


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('---\nname: fictional-example\ndescription: A fictional test capability.\n---\n# Example\nOnly fictional data.\n')
        self.output = self.root / 'output'

    def test_init_packages_and_preserves_source(self):
        before = (self.source / 'SKILL.md').read_bytes()
        result = audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        self.assertIsNone(result['production_ready'])
        self.assertEqual(before, (self.source / 'SKILL.md').read_bytes())
        self.assertTrue((self.output / '.github/workflows/validate.yml').is_file())
        self.assertTrue((self.output / 'README.en.md').is_file())
        self.assertFalse((self.output / 'plugin.mk').exists())
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=self.output, check=True, capture_output=True)
        attach(self.output)
        dry = subprocess.run(['make', '-s', 'install-local', 'TARGET=codex', 'DRY_RUN=1'], cwd=self.output, check=True, capture_output=True, text=True)
        self.assertEqual('codex', json.loads(dry.stdout)['commands'][0][0])
        report = audit.audit(self.output)
        self.assertTrue(report['structurally_valid'])
        self.assertEqual('warning', next(c['status'] for c in report['checks'] if c['id']=='documentation'))
        self.assertIsNone(report['production_ready'])
        self.assertTrue(all(c['status'] == 'pass' for c in report['checks'] if c['id'].startswith('installer:')))
        self.assertFalse(report['target_code_executed'])
        self.assertEqual('needs_attention', report['status'])

    def test_init_refuses_existing_repository_without_changes(self):
        self.output.mkdir()
        target = self.output / 'README.md'
        target.write_text('User content')
        with self.assertRaisesRegex(ValueError, 'not empty'):
            audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        self.assertEqual('User content', target.read_text())
        self.assertEqual([target], list(self.output.iterdir()))

    def test_private_source_and_symlink_output_refused_before_writes(self):
        (self.source / '.env').write_text('FICTIONAL=only')
        with self.assertRaisesRegex(ValueError, 'private/cache'):
            audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        self.assertFalse(self.output.exists())
        (self.source / '.env').unlink()
        self.output.symlink_to(self.root / 'elsewhere')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')

    def test_read_only_audit_finds_duplicate_canonical_sources(self):
        audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        duplicate = self.output / '.claude/skills/fictional-example/SKILL.md'
        duplicate.parent.mkdir(parents=True)
        duplicate.write_bytes((self.source / 'SKILL.md').read_bytes())
        before = {str(p): p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
        report = audit.audit(self.output)
        self.assertFalse(report['structurally_valid'])
        self.assertEqual('fail', next(c['status'] for c in report['checks'] if c['id'] == 'source_of_truth'))
        self.assertEqual(before, {str(p):p.read_bytes() for p in self.output.rglob('*') if p.is_file()})

    def test_verify_detects_installer_drift_without_executing_it(self):
        audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        engine = self.output / 'scripts/plugin.py'
        engine.write_text("raise RuntimeError('must never execute target')\n")
        report = audit.audit(self.output)
        self.assertEqual('fail', next(c['status'] for c in report['checks'] if c['id']=='installer:scripts/plugin.py'))
        self.assertEqual('pass', next(c['status'] for c in report['checks'] if c['id']=='installer:manifest'))

    def test_python_cache_is_not_a_release_blocker_and_is_not_packaged(self):
        import zipfile
        audit.scaffold_plugin(self.source, self.output, languages=['de','en'], repository='https://github.com/example/fictional', author='Fictional Team')
        cache = self.output / 'skills/fictional-example/scripts/__pycache__'
        cache.mkdir(parents=True)
        bytecode = cache / 'fictional.cpython-312.pyc'
        bytecode.write_bytes(b'fictional bytecode fixture')
        import documentation, re
        for name in documentation.page_layout(documentation.language_policy(self.output)):
            page = self.output / name
            page.write_text(re.sub(r'\{\{[^}]+\}\}', 'Fictional example.', page.read_text()))
        report = audit.audit(self.output)
        self.assertTrue(report['structurally_valid'])
        self.assertEqual('pass', next(c['status'] for c in report['checks'] if c['id']=='payload:fictional-example'))
        self.assertEqual(b'fictional bytecode fixture', bytecode.read_bytes())
        attach(self.output)
        subprocess.run(['make', '-s', 'install-local', 'TARGET=codex', 'DRY_RUN=1'], cwd=self.output, check=True, capture_output=True)
        self.assertFalse(list((self.output/'dist').rglob('__pycache__')))
        self.assertFalse(list((self.output/'dist').rglob('*.pyc')))
        # Excluding regular caches must not hide source symlinks or secrets.
        (cache / 'linked.pyc').symlink_to(bytecode)
        self.assertFalse(audit.audit(self.output)['structurally_valid'])

    def test_init_and_audit_accept_english_only_documentation(self):
        import re
        import documentation
        audit.scaffold_plugin(self.source,self.output,languages=['en'])
        self.assertFalse((self.output/'docs/de').exists())
        for name in documentation.page_layout(documentation.language_policy(self.output)):
            page=self.output/name
            page.write_text(re.sub(r'\{\{[^}]+\}\}', 'Fictional example.', page.read_text()))
        report=audit.audit(self.output)
        self.assertEqual('pass',next(c['status'] for c in report['checks'] if c['id']=='documentation'))

    def test_verify_rejects_host_sources_and_custom_roots_without_writes(self):
        audit.scaffold_plugin(self.source, self.output, languages=['en'])
        manifest_path = self.output / 'plugin.json'
        for location in ('.claude/skills', '.agents/skills', 'custom/skills'):
            with self.subTest(location=location):
                destination = self.output / location
                destination.parent.mkdir(parents=True, exist_ok=True)
                (self.output / 'skills').rename(destination)
                manifest = json.loads(manifest_path.read_text())
                manifest['extensions']['io.zyris.distribution']['skillRoot'] = location
                manifest_path.write_text(json.dumps(manifest))
                before = {str(p): p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
                report = audit.audit(self.output)
                self.assertEqual('fail', next(c['status'] for c in report['checks'] if c['id'] == 'neutral_source_layout'))
                self.assertEqual(before, {str(p): p.read_bytes() for p in self.output.rglob('*') if p.is_file()})
                destination.rename(self.output / 'skills')

    def test_init_generates_importable_metadata_and_audit_detects_drift(self):
        audit.scaffold_plugin(self.source, self.output, languages=['en'])
        self.assertTrue((self.output / 'skills/fictional-example/SKILL.md').is_file())
        self.assertFalse((self.output / '.claude').exists())
        self.assertNotIn('version', json.loads((self.output / 'plugin.json').read_text()))
        for relative in ('.claude-plugin/plugin.json',):
            path = self.output / relative
            original = path.read_bytes()
            with self.subTest(relative=relative):
                path.write_text('{}')
                report = audit.audit(self.output)
                self.assertEqual('fail', next(c['status'] for c in report['checks'] if c['id'] == 'installer:manifest'))
                self.assertEqual('{}', path.read_text())
                path.write_bytes(original)
        self.assertEqual('pass', next(c['status'] for c in audit.audit(self.output)['checks'] if c['id'] == 'installer:manifest'))

    def test_make_recipe_drift_and_duplicate_targets_are_reported(self):
        audit.scaffold_plugin(self.source, self.output, languages=['en'])
        makefile = self.output/'Makefile'
        original = makefile.read_text()
        for text in (original.replace('scripts/plugin.py check', 'scripts/plugin.py sync'),
                     original + '\ninstall-local:\n\t@echo unexpected\n',
                     original + '\npackage:\n\t@echo retired\n'):
            makefile.write_text(text)
            report = audit.audit(self.output)
            self.assertEqual('fail', next(c['status'] for c in report['checks'] if c['id'] == 'installer:make'))
            self.assertEqual(text, makefile.read_text())

    def test_explicit_plugin_name_drives_catalogs_without_renaming_skill(self):
        audit.scaffold_plugin(self.source, self.output, languages=['en'], plugin_name='fictional-suite')
        self.assertEqual('fictional-suite', json.loads((self.output/'plugin.json').read_text())['name'])
        for relative in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
            self.assertFalse((self.output/relative).exists())
        self.assertEqual((self.source/'SKILL.md').read_bytes(), (self.output/'skills/fictional-example/SKILL.md').read_bytes())

    def test_invalid_plugin_name_leaves_output_untouched(self):
        with self.assertRaisesRegex(ValueError, 'Plugin name'):
            audit.scaffold_plugin(self.source, self.output, languages=['en'], plugin_name='../invalid')
        self.assertFalse(self.output.exists())

    def test_malformed_manifest_is_reported(self):
        self.output.mkdir()
        (self.output / 'plugin.json').write_text(json.dumps({'name': [], 'description':'example'}))
        self.assertFalse(audit.audit(self.output)['structurally_valid'])


if __name__ == '__main__':
    unittest.main()
