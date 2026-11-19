"""Licensing acceptance using disposable, fictional repositories only."""
import json
import subprocess
import sys
from unittest import TestCase
from tests.support.workflow_fixture import WorkflowFixture, flow


class LicensingTests(WorkflowFixture, TestCase):
    def create_license(self, **options):
        return flow.plugin_create(self.plugin, self.market, skeleton=True, name='new-plugin',
            display_name='Fictional Plugin', author='Not the copyright holder',
            languages=['de', 'en'], default_language='de', **options)

    def snapshot(self):
        return {str(p): p.read_bytes() for root in (self.plugin, self.market)
                for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}

    def test_mit_license_manifests_and_bilingual_docs(self):
        result = self.create_license(license='MIT', copyright_year='2026', copyright_holder='Fictional Rights Holder')
        text = (self.plugin/'LICENSE').read_text()
        self.assertIn('Copyright (c) 2026 Fictional Rights Holder', text)
        self.assertIn('Permission is hereby granted, free of charge', text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', text)
        self.assertNotIn('Not the copyright holder', text)
        for name in ('plugin.json', '.claude-plugin/plugin.json'):
            self.assertEqual('MIT', json.loads((self.plugin/name).read_text())['license'])
        for name in ('README.md', 'README.en.md', 'docs/de/README.md', 'docs/en/README.md'):
            text = (self.plugin/name).read_text()
            self.assertIn('MIT', text)
            self.assertIn('license.md)', text)
            self.assertNotIn('separat zu klären', text)
            self.assertNotIn('Licensing must be resolved separately', text)
        self.assertIn('../LICENSE', (self.plugin/'docs/license.md').read_text())
        self.assertEqual('passed', result['checks']['status'])
        self.assertEqual('implemented', result['checks']['licensing']['status'])
        self.assertTrue(result['checks']['licensing']['valid'])

    def test_explicit_deferral_is_persistent_and_has_no_license(self):
        result = self.create_license(license='deferred')
        self.assertFalse((self.plugin/'LICENSE').exists())
        self.assertNotIn('license', json.loads((self.plugin/'plugin.json').read_text()))
        self.assertIn('ausdrücklich vertagt', (self.plugin/'README.md').read_text())
        self.assertIn('explicitly deferred', (self.plugin/'README.en.md').read_text())
        self.assertIn('explicitly deferred', (self.plugin/'docs/license.md').read_text())
        self.assertEqual('deferred', result['checks']['licensing']['status'])

    def test_missing_decision_or_copyright_and_unsupported_template_do_not_write(self):
        for args in ({}, {'license':'MIT'}, {'license':'MIT', 'copyright_year':'2026'},
                     {'license':'Apache-2.0'}, {'license':'MIT', 'copyright_year':'today', 'copyright_holder':'Fixture'}):
            with self.subTest(args=args):
                before = self.snapshot()
                with self.assertRaises(ValueError): self.create_license(**args)
                self.assertEqual(before, self.snapshot())

    def test_existing_conflicting_license_and_deferral_do_not_write(self):
        (self.plugin/'LICENSE').write_text('Fictional existing license, preserve exactly.\n')
        for args in ({'license':'deferred'}, {'license':'MIT','copyright_year':'2026','copyright_holder':'Fixture'}):
            before = self.snapshot()
            with self.assertRaises(ValueError): self.create_license(**args)
            self.assertEqual(before, self.snapshot())

    def test_explicit_complete_license_file_and_existing_license_are_preserved(self):
        original = b'Fictional acceptance license text. Not legal advice.\n'
        path = self.plugin/'LICENSE.md'; path.write_bytes(original)
        result = self.create_license(license='LicenseRef-Fictional', license_file=path)
        self.assertEqual(original, path.read_bytes())
        self.assertFalse((self.plugin/'LICENSE').exists())
        self.assertEqual('LicenseRef-Fictional', json.loads((self.plugin/'plugin.json').read_text())['license'])
        self.assertEqual('LICENSE.md', result['checks']['licensing']['file'])
        self.assertEqual('passed', result['checks']['status'])

    def test_complete_file_import_and_invalid_sources(self):
        path=self.root/'license.txt'; path.write_text('Copyright <YEAR> <COPYRIGHT HOLDER>\n')
        before=self.snapshot()
        with self.assertRaises(ValueError): self.create_license(license='MIT', license_file=path)
        self.assertEqual(before,self.snapshot())
        path.write_text('Explicit fictional license text.\n')
        link=self.root/'linked.txt'; link.symlink_to(path)
        with self.assertRaises(ValueError): self.create_license(license='LicenseRef-Fictional', license_file=link)
        self.assertEqual(before,self.snapshot())
        result=self.create_license(license='LicenseRef-Fictional', license_file=path)
        self.assertEqual(path.read_bytes(),(self.plugin/'LICENSE').read_bytes())
        self.assertTrue(result['checks']['licensing']['valid'])

    def test_source_import_receives_license_and_doc_links(self):
        result=flow.plugin_create(self.plugin,self.market,self.source,name='new-plugin',display_name='Fixture',
            description='Fictional source',author='Fixture',languages=['en'],license='MIT',
            copyright_year='2026',copyright_holder='Fictional Holder')
        self.assertTrue((self.plugin/'LICENSE').is_file())
        self.assertIn('MIT',(self.plugin/'README.md').read_text())
        self.assertTrue(result['checks']['licensing']['valid'])
        self.assertFalse(result['checks']['documentation']['valid'])  # source prose still requires authoring

    def test_cli_accepts_explicit_mit_inputs(self):
        result=subprocess.run([sys.executable,'-B',str(flow.SKILL/'scripts/workflows.py'),'plugin-create',
            '--root',str(self.plugin),'--marketplace',str(self.market),'--skeleton','--name','new-plugin',
            '--display-name','Fixture','--author','Fixture','--languages','en','--license','MIT',
            '--copyright-year','2026','--copyright-holder','Fictional Holder'],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual('implemented',json.loads(result.stdout)['checks']['licensing']['status'])

    def test_checks_detect_changed_license_metadata_and_decision(self):
        from licensing import plan
        decision = plan(self.plugin, 'MIT', None, '2026', 'Fictional Holder')
        self.create_license(license='MIT', copyright_year='2026', copyright_holder='Fictional Holder')
        for relative, replacement in (('LICENSE', 'changed'), ('docs/license.md', '# Missing decision'),
                                      ('plugin.json', '{}')):
            path = self.plugin/relative; original = path.read_bytes()
            path.write_text(replacement)
            report = flow.creation_checks(self.plugin, self.market, decision)
            self.assertEqual('needs_attention', report['status'])
            self.assertFalse(report['licensing']['valid'])
            path.write_bytes(original)

    def test_existing_readme_is_preserved_and_license_documentation_gap_reported(self):
        original = '# User prose\n'
        (self.plugin/'README.md').write_text(original)
        result = self.create_license(license='MIT', copyright_year='2026', copyright_holder='Fictional Holder')
        self.assertEqual(original, (self.plugin/'README.md').read_text())
        self.assertEqual('needs_attention', result['checks']['status'])
        self.assertFalse(result['checks']['licensing']['valid'])
        self.assertTrue((self.plugin/'LICENSE').is_file())
