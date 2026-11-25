"""Local development install of scripts/local_plugins.py. Managed by plugin-manager; fictional data only."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('local_plugins', ROOT / 'scripts/local_plugins.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
NAMES = ('fictional-alpha', 'fictional-beta')


class LocalPluginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.root = base / 'market'
        (self.root / 'scripts').mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/marketplace.py', self.root / 'scripts/marketplace.py')
        self.checkouts = {name: base / name for name in NAMES}
        entries = []
        for name, path in self.checkouts.items():
            repository = 'https://github.com/example/' + name
            (path / 'skills/example').mkdir(parents=True)
            (path / 'skills/example/SKILL.md').write_text('---\nname: example\ndescription: Fictional.\n---\n# Example\n')
            (path / 'plugin.json').write_text(json.dumps({'name': name, 'description': 'Fictional', 'repository': repository,
                'extensions': {'io.zyris.distribution': {'skillRoot': 'skills', 'catalogs': False}}}))
            entries.append({'name': name, 'displayName': name, 'description': 'Fictional', 'repository': repository + '.git'})
        (self.root / 'marketplace.json').write_text(json.dumps(
            {'name': 'fictional-market', 'displayName': 'Fictional Market', 'owner': {'name': 'Fixture'}, 'plugins': entries}))
        (self.root / '.local').mkdir()
        (self.root / '.local/marketplace.json').write_text(json.dumps(
            {'sources': {name: str(path) for name, path in self.checkouts.items()}}))
        self.skill = self.checkouts[NAMES[1]] / 'skills/example/SKILL.md'

    def install(self, target='codex'):
        return engine.install_local(target, dry_run=True, root=self.root)

    def test_both_hosts_use_one_development_catalog_with_local_sources_only(self):
        with patch.object(engine.subprocess, 'run') as run:
            for host in ('claude', 'codex'):
                result = self.install(host)
                self.assertEqual('fictional-market-dev', result['marketplace'])
                self.assertEqual(set(NAMES), set(result['plugins']))
                self.assertEqual(len(NAMES) + 1, len(result['commands']))
                self.assertNotIn('https://', str(result['commands']))
                catalog = Path(result['path']) / ('.claude-plugin/marketplace.json' if host == 'claude' else '.agents/plugins/marketplace.json')
                for item in json.loads(catalog.read_text())['plugins']:
                    source = item['source'] if host == 'claude' else item['source']['path']
                    self.assertEqual('./plugins/' + item['name'], source)
            run.assert_not_called()

    def test_an_edit_changes_the_snapshot_of_the_affected_plugin_only(self):
        first = self.install()
        self.skill.write_text('Changed fictional skill')
        second = self.install()
        self.assertEqual(first['plugins'][NAMES[0]]['version'], second['plugins'][NAMES[0]]['version'])
        self.assertNotEqual(first['plugins'][NAMES[1]]['version'], second['plugins'][NAMES[1]]['version'])
        copied = Path(second['path']) / 'plugins' / NAMES[1] / 'skills/example/SKILL.md'
        self.assertEqual('Changed fictional skill', copied.read_text())

    def test_a_missing_checkout_keeps_the_previous_snapshot_and_runs_nothing(self):
        path = Path(self.install('claude')['path'])
        before = {str(p): p.read_bytes() for p in path.rglob('*') if p.is_file()}
        (self.root / '.local/marketplace.json').unlink()
        with patch.object(engine.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'Missing local checkout'):
                engine.install_local('claude', root=self.root)
            run.assert_not_called()
        self.assertEqual(before, {str(p): p.read_bytes() for p in path.rglob('*') if p.is_file()})

    def test_a_foreign_destination_is_not_replaced(self):
        output = self.root / 'dist/local-development/claude-marketplace'
        output.mkdir(parents=True)
        (output / 'keep').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'unowned'):
            self.install('claude')
        self.assertEqual('preserve', (output / 'keep').read_text())

    def test_host_errors_propagate(self):
        with patch.object(engine.shutil, 'which', return_value='claude'), \
                patch.object(engine.subprocess, 'run', side_effect=subprocess.CalledProcessError(7, ['claude'])):
            with self.assertRaises(subprocess.CalledProcessError):
                engine.install_local('claude', root=self.root)

    def test_the_example_file_is_never_runtime_configuration(self):
        (self.root / 'local-marketplace.example.json').write_text('{broken optional example')
        self.assertEqual('fictional-market-dev', self.install()['marketplace'])

    def test_a_branch_switch_keeps_the_catalog_and_takes_the_current_checkout(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.checkouts[NAMES[1]]), '-c', 'user.name=Fixture',
                            '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                            '-c', 'core.hooksPath=/dev/null', *args], check=True, capture_output=True)
        git('init', '-q')
        git('add', '--', 'plugin.json', 'skills')
        git('commit', '-qm', 'Fictional base')
        git('branch', '-M', 'main')
        first = self.install()
        git('switch', '-q', '-c', 'fictional-branch')
        self.skill.write_text(self.skill.read_text() + 'Committed on the branch.\n')
        git('commit', '-qam', 'Fictional change')
        self.skill.write_text(self.skill.read_text() + 'Not committed.\n')
        changed = self.install()
        self.assertEqual(first['path'], changed['path'])
        copied = Path(changed['path']) / 'plugins' / NAMES[1] / 'skills/example/SKILL.md'
        self.assertEqual(self.skill.read_bytes(), copied.read_bytes())
        git('checkout', '-q', '--', 'skills')
        git('switch', '-q', 'main')
        self.assertEqual(first['plugins'][NAMES[1]]['version'], self.install()['plugins'][NAMES[1]]['version'])


if __name__ == '__main__':
    unittest.main()
