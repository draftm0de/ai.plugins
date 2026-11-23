"""State dispatch: language -> skeleton -> configuration -> ready; fictional projects only."""
import json
import shutil
import unittest

from tests.support.workflow_fixture import WorkflowFixture  # puts the Manager scripts on sys.path
from tests.support import project_setup_fixture as fx
from tests.support.project_setup_fixture import FILES, LOCK, Sandbox, tree

RULE = '/.project/operator.json'


class FreshBase(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(configured=False); self.addCleanup(self.box.close)  # no evidence: not configured
        self.p = self.box.project
        (self.p / 'plugin.json').unlink()

    def git_idea(self):
        (self.p / '.git').mkdir(); (self.p / '.git/HEAD').write_text('ref: refs/heads/main\n')
        (self.p / '.idea').mkdir(); (self.p / '.idea/workspace.xml').write_text('<x/>')

    def call(self, *args, **kw):
        return self.box.call(*args, **kw)

    def status(self):
        code, data, _ = self.call('status')
        self.assertEqual(0, code, data)
        return data

    def flow(self, operation, *args):
        code, data, result = self.call(operation, *args)
        self.assertEqual((0, True, 'status'), (code, data['ok'], data['next']), result.stderr + result.stdout)
        return data


class DispatchTests(FreshBase):
    """Target detection and conflicts on the complete isolated Manager copy (delivery/integration). The sequence
    and sync rules of the managed files are tested on a fictional parent in test_sync.py/test_removal.py."""
    def test_empty_and_git_idea_folders_report_language_need_without_writes(self):
        self.git_idea()
        empty = self.box.base / 'empty'; empty.mkdir()
        for target in (self.p, empty):
            before, manager = tree(target), tree(self.box.manager)
            _, data, _ = self.call('status', target=target)
            self.assertEqual(('unconfigured', False, 'language', True), (data['state'], data['plugin_configured'], data['next'], data['ok']))
            self.assertTrue(data['language']['needs_choice'])
            self.assertEqual((before, manager), (tree(target), tree(self.box.manager)))
            self.assertFalse((target / 'plugin.json').exists())

    def test_conflicts_stop_for_every_operation_without_writes(self):
        def foreign_top(): (self.p / 'README.md').write_text('mine'); (self.p / 'src').mkdir()
        def foreign_in_scripts(): (self.p / 'scripts').mkdir(); (self.p / 'scripts/own.py').write_text('x')
        def foreign_skill(): (self.p / 'skills/x').mkdir(parents=True)
        def foreign_project(): (self.p / '.project').mkdir(exist_ok=True); (self.p / '.project/x.txt').write_text('x')
        def bad_json(): (self.p / 'plugin.json').write_text('{bad')
        def manifest_dir(): (self.p / 'plugin.json').mkdir()
        def marketplace(): (self.p / 'marketplace.json').write_text('{}')
        def idea_file(): (self.p / '.idea').write_text('f')
        def git_symlink(): (self.box.base / 'moved').mkdir(); (self.p / '.git').symlink_to(self.box.base / 'moved')
        def bad_language(): (self.p / '.project').mkdir(exist_ok=True); (self.p / '.project/operator.json').write_text('{broken')
        def bad_lock(): (self.p / LOCK).parent.mkdir(parents=True, exist_ok=True); (self.p / LOCK).write_text('{"schema_version": 9, "files": {}}')
        def scripts_symlink(): (self.box.base / 'elsewhere').mkdir(); (self.p / 'scripts').symlink_to(self.box.base / 'elsewhere')
        def ignore_symlink():
            (self.box.base / 'shared.txt').write_text('x\n'); (self.p / '.gitignore').symlink_to(self.box.base / 'shared.txt')
        cases = [foreign_top, foreign_in_scripts, foreign_skill, foreign_project, bad_json, manifest_dir, marketplace,
                 idea_file, git_symlink, bad_language, bad_lock, scripts_symlink, ignore_symlink]
        for build in cases:
            with self.subTest(build.__name__):
                for child in list(self.p.iterdir()):
                    shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
                for extra in ('moved', 'elsewhere', 'shared.txt'):
                    path = self.box.base / extra
                    shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
                build()
                before = tree(self.p)
                for operation, extra in (('status', ()), ('setup', ()), ('language', ('--language', 'de'))):
                    code, data, _ = self.call(operation, *extra)
                    self.assertEqual((1, 'conflict', 'stop'), (code, data['state'], data['next']), (build.__name__, operation))
                    self.assertEqual(before, tree(self.p))
        # the occupied-folder case also names the entries
        for child in list(self.p.iterdir()):
            shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
        foreign_top()
        conflict = self.call('status')[1]['conflicts'][0]
        self.assertEqual(('not_fresh', ['README.md', 'src']), (conflict['code'], conflict['entries']))


class LanguageStepTests(FreshBase):
    def test_saves_language_and_rule_without_touching_metadata(self):
        self.git_idea()
        (self.p / '.gitignore').write_text('build/\n')
        git, idea = (self.p / '.git/HEAD').read_bytes(), (self.p / '.idea/workspace.xml').read_bytes()
        data = self.flow('language', '--language', 'de')
        self.assertEqual((True, ['.project']), (data['language']['saved'], data['created']['directories']))
        self.assertEqual('build/\n' + RULE + '\n', (self.p / '.gitignore').read_text())
        self.assertEqual({'schema_version': 1, 'operator_language': 'de'}, json.loads((self.p / '.project/operator.json').read_text()))
        self.assertEqual((git, idea), ((self.p / '.git/HEAD').read_bytes(), (self.p / '.idea/workspace.xml').read_bytes()))
        self.assertFalse((self.p / 'plugin.json').exists() or (self.p / LOCK).exists() or (self.p / 'scripts').exists())
        self.assertFalse(any(self.p.rglob('__pycache__')))
        before = tree(self.p)
        self.flow('language', '--language', 'de')  # repeat: nothing written
        self.assertEqual(before, tree(self.p))

    def test_conflicting_or_invalid_language_stops_before_writes(self):
        before = tree(self.p)
        self.assertEqual(1, self.call('language', '--language', 'Deutsch!')[0])
        self.assertEqual(before, tree(self.p))
        self.flow('language', '--language', 'de')
        before = tree(self.p)
        self.assertEqual(1, self.call('language', '--language', 'en')[0])
        self.assertEqual(before, tree(self.p))


class GuidedConfigurationTests(WorkflowFixture, unittest.TestCase):
    """Configuration with the existing generator after language and skeleton, in the same folder."""
    def setUp(self):
        super().setUp()
        self.box = Sandbox().make(); self.addCleanup(self.box.close)
        (self.plugin / '.idea').mkdir(); (self.plugin / '.idea/workspace.xml').write_text('<x/>')
        (self.plugin / '.gitignore').write_text('local-notes/\n')
        self.ps = fx.load_state()

    def prepare(self):
        # R17: language first, then configuration; no skeleton exists before the kind is known
        self.assertEqual('language', self.ps.status(str(self.plugin))['next'])
        self.assertTrue(self.ps.language_only(str(self.plugin), 'de')['ok'])
        self.assertEqual('configure', self.ps.status(str(self.plugin))['next'])
        for operation in (lambda: self.ps.setup(str(self.plugin)),):
            with self.assertRaises(self.ps.Conflict) as caught:
                operation()
            self.assertEqual('not_configured', caught.exception.code)

    def finish(self):
        """Evidence of the successful configuration run (R15), written only after the generator succeeded."""
        self.assertTrue(self.ps.record(str(self.plugin), 'plugin', 'new-plugin')['ok'])

    def test_generator_then_evidence_then_skeleton_then_ready(self):
        self.prepare()
        kept = {r: (self.plugin / r).read_bytes() for r in ('.project/operator.json', '.git/HEAD', '.idea/workspace.xml')}
        self.create()  # existing generator, exact selected folder, explicit marketplace
        self.assertEqual('configure', self.ps.status(str(self.plugin))['next'])  # no evidence before a passed run
        self.finish()
        for relative, data in kept.items():
            self.assertEqual(data, (self.plugin / relative).read_bytes(), relative)
        lines = (self.plugin / '.gitignore').read_text().splitlines()
        self.assertEqual((1, True), (lines.count(RULE), 'local-notes/' in lines))
        status = self.ps.status(str(self.plugin))
        self.assertEqual(('plugin', 'skeleton', True, 'new-plugin'), (status['state'], status['next'], status['plugin_configured'], status['plugin']))
        self.assertTrue(self.ps.setup(str(self.plugin))['ok'])
        status = self.ps.status(str(self.plugin))
        self.assertEqual(('ready', False), (status['next'], status['sync']['needed']))
        for relative in FILES:
            self.assertEqual(fx.template(relative), (self.plugin / relative).read_bytes(), relative)
        again = self.ps.setup(str(self.plugin))
        self.assertTrue(again['ok'] and again['matches_template'] and not again['lock']['changed'])

    def test_skeleton_file_before_configuration_is_not_fresh_and_stops_before_the_generator(self):
        self.prepare()
        (self.plugin / 'scripts').mkdir()
        (self.plugin / 'scripts/plugin.py').write_bytes(b'my own version')
        with self.assertRaises(self.ps.Conflict) as caught:
            self.ps.status(str(self.plugin))
        self.assertEqual('not_fresh', caught.exception.code)

    def test_generator_license_rules_still_apply(self):
        self.prepare()
        before = tree(self.plugin)
        import workflows as flow
        with self.assertRaises(ValueError):
            flow.create_plugin(self.plugin, self.market, skeleton=True, name='new-plugin', display_name='Fictional Plugin',
                               description='d', author='a', languages=['de'], default_language='de')  # no license decision
        self.assertEqual(before, tree(self.plugin))

    def test_foreign_content_blocks_before_configuration_is_offered(self):
        (self.plugin / 'README.md').write_text('existing project')
        with self.assertRaises(self.ps.Conflict) as caught:
            self.ps.status(str(self.plugin))
        self.assertEqual('not_fresh', caught.exception.code)
