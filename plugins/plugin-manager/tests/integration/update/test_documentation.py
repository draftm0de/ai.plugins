import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
SPEC = importlib.util.spec_from_file_location('documentation', ROOT / 'skills/_shared/scripts/documentation.py')
doc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doc)


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('---\nname: fictional-demo\n---\n# Demo\nA fictional test skill.\n')
        self.output = self.root / 'output'

    def give_icon(self, output=None):
        """The plugin's one icon: the documentation only references it and never copies it."""
        icon = Path(output or self.output) / 'assets/icon.png'
        icon.parent.mkdir(parents=True, exist_ok=True)
        icon.write_bytes(b'fictional icon')

    def fill(self):
        for name in doc.outline():
            path = self.output / name
            text = path.read_text()
            text = re.sub(r'\{\{[^}]+\}\}', 'Verified fictional example.', text)
            path.write_text(text)

    def test_scaffold_never_writes_an_unsupported_internal_source_pointer(self):
        for relative in ('legacy-skill','.claude/skills/example'):
            with tempfile.TemporaryDirectory() as directory:
                repo=Path(directory);source=repo/relative;source.mkdir(parents=True)
                (source/'SKILL.md').write_text('---\nname: example\n---\n')
                before={str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError,'Unsupported source layout'):
                    doc.scaffold(source,repo,languages=['en'])
                self.assertEqual(before,{str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()})

    def test_the_removed_source_pointer_is_rejected_with_a_reason_and_nothing_is_converted(self):  # R29
        repo = self.root/'repository';(repo/'docs').mkdir(parents=True)
        (repo/'skills/one').mkdir(parents=True);(repo/'skills/one/SKILL.md').write_text('---\nname: one\n---\n')
        manifest = repo/'docs/documentation.json'
        text = json.dumps({'schema_version':1,'source_skill':'skills/one','documentation':{'languages':['en'],'default_language':'en'}})
        manifest.write_text(text)
        for call in (lambda: doc.scaffold(repo, self.output, languages=['en']), lambda: doc.inspect(repo)):
            with self.assertRaisesRegex(ValueError, 'Unsupported field source_skill'):
                call()
        self.assertFalse(self.output.exists())
        self.assertEqual(text, manifest.read_text())

    def test_standalone_frontmatter_never_bypasses_source_preflight(self):
        (self.source/'.claude/skills').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'Unsupported source layout'):
            doc.scaffold(self.source,self.output,languages=['en'])
        self.assertFalse(self.output.exists())
        (self.source/'.claude/skills').rmdir()
        (self.source/'docs').mkdir()
        (self.source/'docs/documentation.json').write_text('{"schema_version":true}')
        with self.assertRaisesRegex(ValueError,'Invalid documentation manifest'):
            doc.scaffold(self.source,self.output,languages=['en'])
        self.assertFalse(self.output.exists())

    def test_noninteger_schema_rejected_before_scaffolding(self):
        (self.output/'docs').mkdir(parents=True)
        path = self.output/'docs/documentation.json'
        for version in (True,1.0):
            path.write_text(json.dumps({'schema_version':version,'documentation':{'languages':['en'],'default_language':'en'}}))
            before = {str(p):p.read_bytes() for p in self.output.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Invalid documentation manifest'):
                doc.scaffold(self.source,self.output,languages=['en'])
            self.assertEqual(before, {str(p):p.read_bytes() for p in self.output.rglob('*') if p.is_file()})

    def test_obsolete_source_layout_and_language_inference_are_rejected(self):
        repo = self.root / 'repository'
        old = repo / '.claude/skills/example'
        old.mkdir(parents=True)
        (old / 'SKILL.md').write_text('---\nname: example\n---\n')
        with self.assertRaisesRegex(ValueError, 'Unsupported source layout'):
            doc.source_skills(repo)
        (repo / 'SKILL.md').write_text('# Old pointer')
        with self.assertRaisesRegex(ValueError, 'Unsupported source layout'):
            doc.source_skills(repo)
        (repo / 'docs/de').mkdir(parents=True)
        (repo / 'docs/en').mkdir()
        (repo / 'README.en.md').write_text('Existing content')
        (repo / 'docs/documentation.json').write_text(json.dumps({'schema_version':1,'extra_sources':[]}))
        before = {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'explicit documentation'):
            doc.language_policy(repo)
        self.assertEqual(before, {str(p):p.read_bytes() for p in repo.rglob('*') if p.is_file()})

    def test_scaffold_is_bilingual_preserves_existing_and_references_the_single_icon(self):
        result = doc.scaffold(self.source, self.output, languages=['de','en'])
        self.assertEqual(len(doc.outline()), 8)
        self.assertEqual(len(result['created']), 9)  # documentation.json, two READMEs and six pages
        self.assertFalse((self.output / 'docs/assets').exists())  # no second copy of the icon
        self.assertIn('assets/icon.png', (self.output / 'README.md').read_text())
        self.assertIn('assets/icon.png is missing', ' '.join(doc.validate(self.output)))
        self.give_icon()
        self.assertNotIn('assets/icon.png is missing', ' '.join(doc.validate(self.output)))
        (self.output / 'README.md').write_text('Existing user content')
        self.assertEqual(doc.scaffold(self.source, self.output, languages=['de','en'])['created'], [])
        self.assertEqual((self.output / 'README.md').read_text(), 'Existing user content')

    def test_validation_rejects_unwritten_scaffold_then_accepts_complete_structure(self):
        doc.scaffold(self.source, self.output, languages=['de','en'])
        self.assertTrue(any('placeholders' in item for item in doc.validate(self.output)))
        self.fill()
        self.give_icon()
        self.assertEqual(doc.validate(self.output), [])

    def test_validation_detects_broken_links_missing_locale_and_heading_drift(self):
        doc.scaffold(self.source, self.output, languages=['de','en'])
        self.fill()
        page = self.output / 'docs/en/installation.md'
        page.write_text(page.read_text().replace('## Update', '## Changed heading') + '\n[Broken](missing.md)\n')
        (self.output / 'README.en.md').unlink()
        errors = '\n'.join(doc.validate(self.output))
        self.assertIn('missing page', errors)
        self.assertIn('missing link target', errors)
        self.assertIn('headings', errors)

    def test_validation_checks_language_switch_and_anchor(self):
        doc.scaffold(self.source, self.output, languages=['de','en'])
        self.fill()
        page = self.output / 'docs/en/installation.md'
        page.write_text(page.read_text().replace('[Deutsch](../de/installation.md)', 'Deutsch') + '\n[Missing section](concepts.md#does-not-exist)\n')
        errors = '\n'.join(doc.validate(self.output))
        self.assertIn('counterpart', errors)
        self.assertIn('heading anchor', errors)

    def test_refuses_skill_output_symlinks(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            doc.scaffold(self.source, self.source, languages=['de','en'])
        self.output.mkdir()
        (self.output / 'docs').symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            doc.scaffold(self.source, self.output, languages=['de','en'])
        self.assertFalse((self.output / 'README.md').exists())

    def test_english_and_german_templates_have_localized_headings(self):
        outline = doc.outline()
        self.assertEqual(outline['README.md'][0], 'Was es tut')
        self.assertEqual(outline['README.en.md'][0], 'What it does')
        self.assertEqual(['Überblick'], outline['docs/de/skills.md'])
        self.assertEqual(['Overview'], outline['docs/en/skills.md'])

    def test_every_skill_of_the_repository_and_the_scope_are_documentation_sources(self):  # R29
        repo = self.root / 'repository'
        for name in ('one', 'two'):
            (repo / 'skills' / name / 'flows').mkdir(parents=True)
            (repo / 'skills' / name / 'SKILL.md').write_text('---\nname: %s\n---\n' % name)
            (repo / 'skills' / name / 'flows/x.md').write_text('flow')
        (repo / 'SCOPE.md').write_text('# Scope')
        info = doc.inspect(repo)
        self.assertEqual(['skills/one/SKILL.md', 'skills/one/flows/x.md', 'skills/two/SKILL.md', 'skills/two/flows/x.md', 'SCOPE.md'], info['evidence_files'])
        self.assertEqual(2, len(info['skills']))
        doc.scaffold(repo, repo, languages=['de','en'])
        data = json.loads((repo / 'docs/documentation.json').read_text())
        self.assertNotIn('source_skill', data)  # no pointer to one skill is written
        data['features'] = ['A duplicated unsupported claim']
        (repo / 'docs/documentation.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'not duplicated'):
            doc.inspect(repo)

    def test_a_repository_without_a_skill_is_rejected(self):
        repo = self.root / 'empty'
        repo.mkdir()
        with self.assertRaisesRegex(ValueError, 'No skill found'):
            doc.inspect(repo)

    def test_single_language_and_english_default_layouts(self):
        for languages, default in ((['en'],'en'), (['de'],'de'), (['en','de'],'en')):
            with self.subTest(languages=languages):
                output = self.root / ('-'.join(languages))
                doc.scaffold(self.source, output, languages=languages, default_language=default)
                policy = doc.language_policy(output)
                pages = doc.page_layout(policy)
                self.assertEqual(4 * len(languages),len(pages))
                for name in pages:
                    path = output / name
                    path.write_text(re.sub(r'\{\{[^}]+\}\}', 'Fictional example.', path.read_text()))
                self.give_icon(output)
                self.assertEqual([],doc.validate(output))
                self.assertIn('## Who it is for' if default=='en' else '## Für wen',(output/'README.md').read_text())
                if len(languages)==1:
                    self.assertFalse((output/'README.en.md').exists())
                    self.assertFalse((output/'README.de.md').exists())
                    other='de' if default=='en' else 'en'
                    self.assertFalse((output/'docs'/other).exists())
                else:
                    self.assertTrue((output/'README.de.md').is_file())
                self.assertEqual([],doc.scaffold(self.source,output)['created'])

    def test_policy_rejects_invalid_or_conflicting_choices_before_writes(self):
        for languages,default in (([], 'en'),(['en','en'],'en'),(['fr'],'fr'),(['en'],'de')):
            with self.assertRaises(ValueError):
                doc.scaffold(self.source,self.output,languages=languages,default_language=default)
            self.assertFalse(self.output.exists())
        doc.scaffold(self.source,self.output,languages=['en'])
        (self.output/'README.md').write_text('Preserve this text')
        with self.assertRaisesRegex(ValueError,'conflicts'):
            doc.scaffold(self.source,self.output,languages=['de'])
        self.assertEqual('Preserve this text',(self.output/'README.md').read_text())

    def test_selected_language_cannot_hide_broken_links(self):
        doc.scaffold(self.source,self.output,languages=['en'])
        for name in doc.page_layout(doc.language_policy(self.output)):
            path=self.output/name
            path.write_text(re.sub(r'\{\{[^}]+\}\}', 'Fictional example.', path.read_text()))
        page=self.output/'README.md'
        page.write_text(page.read_text()+'\n[Accidental unselected language](README.de.md)\n')
        self.assertIn('missing link target','\n'.join(doc.validate(self.output)))

    def test_new_project_requires_language_decision_before_writes(self):
        with self.assertRaisesRegex(ValueError,'Choose documentation languages'):
            doc.scaffold(self.source,self.output)
        self.assertFalse(self.output.exists())

    def installation_repo(self, origin='git@github.com:example/market.git'):
        repo, market = self.root / 'repository', self.root / 'market'
        (repo / 'skills/one').mkdir(parents=True)
        (repo / 'skills/one/SKILL.md').write_text('---\nname: one\ndescription: One.\n---\n')
        (repo / 'plugin.json').write_text(json.dumps({'name': 'demo', 'extensions': {'com.openai': {'interface': {'displayName': 'Demo Tool'}}}}))
        market.mkdir()
        (market / 'marketplace.json').write_text(json.dumps({'name': 'demo-market', 'plugins': []}))
        subprocess.run(['git', 'init', '-q', str(market)], check=True)
        if origin:
            subprocess.run(['git', '-C', str(market), 'remote', 'add', 'origin', origin], check=True)
        evidence = repo / '.project/plugins/plugin-manager'
        evidence.mkdir(parents=True)
        (evidence / 'config.json').write_text(json.dumps({'schema_version': 2, 'marketplace': {'name': 'demo-market'}}))
        (evidence / 'local.json').write_text(json.dumps({'schema_version': 1, 'marketplace_path': '../market'}))
        self.give_icon(repo)
        return repo

    def test_the_installation_page_is_filled_from_the_repository_facts_and_the_address_is_recorded(self):  # R35
        repo = self.installation_repo()
        result = doc.scaffold(repo, repo, languages=['en', 'de'])
        self.assertEqual([], result['missing_facts'])
        self.assertEqual('https://github.com/example/market', json.loads((repo / 'docs/documentation.json').read_text())['marketplace_url'])
        for language in ('en', 'de'):
            text = (repo / 'docs' / language / 'installation.md').read_text()
            self.assertNotIn('{{', text)
            for line in ('/plugin marketplace add https://github.com/example/market', '/plugin install demo@demo-market',
                         'codex plugin add demo@demo-market', 'claude plugin marketplace update demo-market',
                         'claude plugin uninstall demo@demo-market', 'codex plugin remove demo@demo-market', 'Demo Tool'):
                self.assertIn(line, text, language)

    def test_an_unknown_address_is_reported_and_never_invented(self):  # R35
        repo = self.installation_repo(origin=None)
        result = doc.scaffold(repo, repo, languages=['en'])
        self.assertEqual(['url'], result['missing_facts'])
        text = (repo / 'docs/en/installation.md').read_text()
        self.assertIn('{{MARKETPLACE_URL}}', text)
        self.assertIn('demo@demo-market', text)
        self.assertNotIn('marketplace_url', json.loads((repo / 'docs/documentation.json').read_text()))
        self.assertIn('placeholders', ' '.join(doc.validate(repo)))

    def test_the_recorded_address_wins_and_only_a_plain_github_address_is_accepted(self):  # R35
        repo = self.installation_repo()
        (repo / 'docs').mkdir()
        manifest = repo / 'docs/documentation.json'
        base = {'schema_version': 1, 'extra_sources': [], 'open_questions': [], 'documentation': {'languages': ['en'], 'default_language': 'en'}}
        manifest.write_text(json.dumps(dict(base, marketplace_url='https://github.com/other/place')))
        doc.scaffold(repo, repo)
        self.assertIn('marketplace add https://github.com/other/place', (repo / 'docs/en/installation.md').read_text())
        for bad in ('https://user:pw@github.com/o/n', 'git@github.com:o/n.git', 'https://example.com/o/n'):
            manifest.write_text(json.dumps(dict(base, marketplace_url=bad)))
            with self.assertRaisesRegex(ValueError, 'marketplace_url'):
                doc.language_policy(repo)

