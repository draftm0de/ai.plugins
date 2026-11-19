"""End-to-end creation/configuration using fictional repositories and isolated hosts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests.support.plugin_fixture import materialize

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(ROOT/'skills/_shared/scripts'))
import workflows as flow
import verify

from tests.support.workflow_fixture import WorkflowFixture

class PluginCreateWorkflowTests(WorkflowFixture, unittest.TestCase):
    def test_old_host_layout_rejected_before_creating_plugin(self):
        for relative in ('.claude/skills','.agents/skills','.claude-plugin/marketplace.json','.agents/plugins/marketplace.json','.codex-plugin/marketplace.json'):
            path = self.plugin/relative; path.mkdir(parents=True)
            (path/'existing.txt').write_text('preserve this source')
            before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError,'Unsupported host-local'):
                self.create()
            self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})
            (path/'existing.txt').unlink();path.rmdir()

    def test_existing_architecture_conflict_rejected_without_changes(self):
        (self.plugin/'docs').mkdir()
        (self.plugin/'docs/architecture.md').write_text('Conflicting project rules')
        before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Existing content differs'):
            self.create()
        self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_boolean_documentation_schema_rejected_before_creation(self):
        (self.plugin/'docs').mkdir()
        (self.plugin/'docs/documentation.json').write_text(json.dumps({'schema_version':True,'documentation':{'languages':['en'],'default_language':'en'}}))
        before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Invalid documentation manifest'):
            self.create()
        self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_create_rejects_existing_invalid_documentation_policy_before_writes(self):
        docs = self.plugin/'docs'; docs.mkdir()
        (docs/'documentation.json').write_text('{"schema_version":1}')
        before = {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'explicit documentation'):
            self.create()
        self.assertEqual(before, {str(p):p.read_bytes() for base in (self.plugin,self.market) for p in base.rglob('*') if p.is_file()})

    def test_collisions_and_wrong_origins_preserve_files(self):
        (self.plugin/'scripts').mkdir();(self.plugin/'scripts/plugin.py').write_text('personal tooling')
        before=(self.market/'marketplace.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'Existing content differs'):self.create()
        self.assertFalse((self.plugin/'plugin.json').exists())
        self.assertEqual(before,(self.market/'marketplace.json').read_bytes())
        with self.assertRaisesRegex(ValueError,'conflicts'):
            flow.marketplace_create(self.market,repository='https://github.com/example/wrong')


    def test_clone_missing_checkout_and_no_remote_creation(self):
        destination=self.root/'cloned'
        remote=self.root/'fixture.git'
        subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
        # A command-scoped Git rewrite exercises real clone without any network.
        env={'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'url.'+remote.as_uri()+'.insteadOf',
             'GIT_CONFIG_VALUE_0':'https://github.com/example/cloned.git',
             'GIT_CONFIG_KEY_1':'protocol.file.allow','GIT_CONFIG_VALUE_1':'always'}
        with patch.dict(os.environ,env):
            flow.plugin_create(destination,self.market,self.source,name='cloned',display_name='Fictional',description='Fixture',repository='https://github.com/example/cloned',author='Fixture',languages=['en'], license='deferred')
        self.assertTrue((destination/'.git').is_dir())
        self.assertTrue(verify.verify(destination)['valid'])
        self.assertEqual('https://github.com/example/cloned.git',subprocess.check_output(['git','-C',str(destination),'remote','get-url','origin'],text=True).strip())


    def test_create_preserves_symlinks_and_missing_facts_fail(self):
        (self.plugin/'scripts').symlink_to(self.source,target_is_directory=True)
        before={p.name:p.read_bytes() for p in self.source.iterdir()}
        with self.assertRaisesRegex(ValueError,'Symlink'): self.create()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.source.iterdir()})
        self.assertFalse((self.plugin/'plugin.json').exists())
        with self.assertRaisesRegex(ValueError,'Display name'):
            flow.plugin_create(self.plugin,self.market,self.source,author='Fixture',description='Fixture',languages=['en'], license='deferred')


    def test_nested_ignore_conflict_blocks_plugin_creation_before_writes(self):
        (self.plugin/'.gitignore').write_text('.local/\n!.local/\n.local/*\n')
        (self.plugin/'.local').mkdir()
        (self.plugin/'.local/.gitignore').write_text('!marketplace.json\n')
        before=(self.market/'marketplace.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'Ineffective Git ignore'):self.create()
        self.assertFalse((self.plugin/'plugin.json').exists())
        self.assertFalse((self.plugin/'.local/marketplace.json').exists())
        self.assertEqual(before,(self.market/'marketplace.json').read_bytes())



    def test_generated_repositories_use_layered_test_commands(self):
        self.create()
        for repository, count in ((self.plugin, 2), (self.market, 1)):
            result = subprocess.run(['make', 'test', 'TEST_GROUP='], cwd=repository, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('Ran ' + str(count) + ' test', result.stderr)
            self.assertTrue((repository/'tests/contracts/test_structure.py').is_file())
            self.assertFalse((repository/'tests/test_structure.py').exists())

    def test_confirmed_inputs_create_skeleton_and_association_without_commit(self):
        source_bytes = (self.source/'SKILL.md').read_bytes()
        result = self.create()
        self.assertFalse(result['published'])
        self.assertIn('Complete documentation', result['next'])
        manifest = json.loads((self.plugin/'plugin.json').read_text())
        self.assertEqual('new-plugin', manifest['name'])
        self.assertEqual('Fictional Plugin', manifest['extensions']['com.openai']['interface']['displayName'])
        self.assertEqual('https://github.com/example/new-plugin', manifest['repository'])
        self.assertEqual(source_bytes, (self.plugin/'skills/fictional-skill/SKILL.md').read_bytes())
        for relative in ('README.md', 'README.en.md', 'docs/documentation.json',
                         '.claude-plugin/plugin.json',
                         'scripts/run_tests.py', 'tests/contracts/test_structure.py'):
            self.assertTrue((self.plugin/relative).is_file(), relative)
        config = json.loads((self.market/'marketplace.json').read_text())
        self.assertEqual('new-plugin', config['plugins'][0]['name'])
        self.assertEqual('https://github.com/example/new-plugin.git', config['plugins'][0]['repository'])
        for repository in (self.plugin, self.market):
            report = verify.verify(repository)
            self.assertTrue(report['structure_valid'], report)
            self.assertTrue(report['local_development']['complete'], report)
            self.assertNotEqual(0, subprocess.run(['git', '-C', str(repository), 'rev-parse', '--verify', 'HEAD'],
                                                 capture_output=True).returncode)
        for relative in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
            self.assertFalse((self.plugin/relative).exists())

    def test_missing_skill_source_does_not_create_a_functional_placeholder(self):
        before = {str(p.relative_to(self.market)): p.read_bytes() for p in self.market.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(self.market).parts}
        with self.assertRaisesRegex(ValueError, 'accessible local directory'):
            flow.plugin_create(self.plugin, self.market, self.root/'missing-skill', name='new-plugin',
                               display_name='Fictional Plugin', description='Confirmed description',
                               author='Fictional Publisher', languages=['en'], license='deferred')
        self.assertEqual([], [p for p in self.plugin.iterdir() if p.name != '.git'])
        after = {str(p.relative_to(self.market)): p.read_bytes() for p in self.market.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(self.market).parts}
        self.assertEqual(before, after)

    def test_skeleton_without_domain_source_has_scope_rules_and_local_association(self):
        result = flow.plugin_create(self.plugin, self.market, skeleton=True, name='new-plugin',
                                   display_name='Fictional Plugin', author='Fictional Publisher', languages=['en'], license='deferred')
        self.assertEqual('skeleton', result['implementation_status'])
        self.assertFalse(result['published'])
        for relative in ('SCOPE.md', 'AGENTS.md', 'CLAUDE.md', 'docs/architecture.md'):
            self.assertTrue((self.plugin/relative).is_file(), relative)
        self.assertIn('Status: draft', (self.plugin/'SCOPE.md').read_text())
        skill = (self.plugin/'skills/new-plugin/SKILL.md').read_text()
        self.assertIn('<!-- plugin-skeleton: unimplemented -->', skill)
        self.assertNotIn('Fictional acceptance capability', skill)
        report = verify.verify(self.plugin)
        self.assertTrue(report['structure_valid'])
        self.assertEqual('skeleton', report['implementation_status'])
        self.assertTrue(report['local_development']['complete'])
        review = verify.scope_review(self.plugin)
        self.assertEqual('needs_attention', review['status'])
        self.assertEqual('unverified', review['semantic_status'])
        cli = subprocess.run([sys.executable, '-B', str(flow.SKILL/'scripts/verify.py'),
                              '--source', str(self.plugin), '--review'], capture_output=True, text=True)
        self.assertEqual(1, cli.returncode)
        cli_report = json.loads(cli.stdout)
        self.assertTrue(cli_report['structure_valid'])
        self.assertEqual('needs_attention', cli_report['review']['status'])
        self.assertFalse(cli_report['review']['target_code_executed'])
        self.assertFalse((self.plugin/'LICENSE').exists())
        self.assertNotEqual(0, subprocess.run(['git','-C',str(self.plugin),'rev-parse','--verify','HEAD'],capture_output=True).returncode)

    def test_skeleton_cli_and_conflicting_development_rules(self):
        original = 'User-owned instructions must be preserved\n'
        (self.plugin/'AGENTS.md').write_text(original)
        before = (self.market/'marketplace.json').read_bytes()
        args = [sys.executable, '-B', str(flow.SKILL/'scripts/workflows.py'), 'plugin-create', '--license', 'deferred',
                '--root', str(self.plugin), '--marketplace', str(self.market), '--skeleton',
                '--name', 'new-plugin', '--display-name', 'Fictional Plugin', '--author', 'Fixture', '--languages', 'en']
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(original, (self.plugin/'AGENTS.md').read_text())
        self.assertEqual(before, (self.market/'marketplace.json').read_bytes())
        self.assertFalse((self.plugin/'plugin.json').exists())
        (self.plugin/'AGENTS.md').unlink()  # owned temporary fixture only
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('skeleton', json.loads(result.stdout)['implementation_status'])

    def test_skeleton_and_source_are_mutually_exclusive_before_writes(self):
        with self.assertRaisesRegex(ValueError, 'either'):
            flow.plugin_create(self.plugin, self.market, self.source, skeleton=True, license='deferred')
        self.assertFalse((self.plugin/'plugin.json').exists())

    def test_skeleton_documentation_all_language_policies(self):
        from documentation import validate, page_layout, language_policy
        for index, (languages, default) in enumerate(((['en'], 'en'), (['de'], 'de'),
                                                    (['de', 'en'], 'de'), (['de', 'en'], 'en'))):
            with self.subTest(languages=languages, default=default):
                root = self.repo('skeleton-' + str(index))
                result = flow.plugin_create(root, self.market, skeleton=True, name=root.name,
                    display_name='Fictional Skeleton', author='Fixture', languages=languages, default_language=default, license='deferred')
                self.assertEqual([], validate(root))
                self.assertEqual('passed', result['checks']['status'])
                self.assertEqual('pending', result['checks']['functional_acceptance'])
                self.assertEqual('not_run', result['checks']['tests'])
                self.assertEqual('not_run', result['checks']['host_acceptance'])
                self.assertEqual('deferred', result['checks']['licensing']['status'])
                self.assertTrue((root/'README.md').read_text().startswith('# Fictional Skeleton\n'))
                for path, (_, _, language) in page_layout(language_policy(root)).items():
                    text = (root/path).read_text()
                    self.assertNotIn('{{', text)
                readme = (root/'README.md').read_text()
                self.assertIn('Nicht funktionsfähiges' if default == 'de' else 'Nonfunctional', readme)
                self.assertFalse((root/('README.en.md' if default == 'en' else 'README.de.md')).exists())

    def test_preserved_invalid_docs_are_reported_without_overwrite(self):
        original = '# User-owned draft\n\n{{UNRESOLVED}}\n'
        (self.plugin/'README.md').write_text(original)
        result = flow.plugin_create(self.plugin, self.market, skeleton=True, name='new-plugin',
            display_name='Fictional Plugin', author='Fixture', languages=['en'], license='deferred')
        self.assertEqual(original, (self.plugin/'README.md').read_text())
        self.assertTrue(result['checks']['plugin']['structure_valid'])
        self.assertEqual('needs_attention', result['checks']['status'])
        self.assertFalse(result['checks']['documentation']['valid'])
        self.assertIn('Resolve', result['next'])

    def test_final_checks_detect_host_manifest_drift_without_execution(self):
        flow.plugin_create(self.plugin, self.market, skeleton=True, name='new-plugin',
            display_name='Fictional Plugin', author='Fixture', languages=['en'], license='deferred')
        manifest = self.plugin/'.claude-plugin/plugin.json'
        manifest.write_text('{}')
        report = flow.creation_checks(self.plugin, self.market)
        self.assertEqual('needs_attention', report['status'])
        self.assertFalse(report['plugin']['structure_valid'])
        self.assertTrue(report['documentation']['valid'])
        self.assertEqual('not_run', report['tests'])
