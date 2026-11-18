import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from plugin_fixture import materialize

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('plugin_build', ROOT / 'scripts/plugin.py')
plugin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plugin)


class PluginTests(unittest.TestCase):


    def test_isolated_host_snapshots_bundle_runtime_and_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            for host in ('claude', 'codex'):
                installed = materialize(Path(directory)/host, host)
                files = {str(p.relative_to(installed)): p.read_bytes() for p in installed.rglob('*') if p.is_file()}
                key = '.claude-plugin/plugin.json' if host == 'claude' else '.codex-plugin/plugin.json'
                self.assertIn(key, files)
                self.assertNotIn('install.sh', files)
                self.assertFalse(any(n.startswith(('tests/', '.git/')) for n in files))
                prefix = 'skills/plugin-manager/'
                for name in ('SKILL.md', 'scripts/documentation.py', 'templates/plugin/Makefile', 'templates/docs/de/development.md'):
                    self.assertIn(prefix + name, files)
                self.assertNotIn(prefix + 'templates/plugin/plugin.mk', files)
                self.assertEqual(files['assets/icon.png'], files[prefix + 'assets/icon.png'])
                materialize(installed, host)
                self.assertEqual(files, {str(p.relative_to(installed)): p.read_bytes() for p in installed.rglob('*') if p.is_file()})

    def test_runtime_change_changes_cache_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ('skills', 'assets'):
                shutil.copytree(ROOT / folder, root / folder)
            shutil.copy2(ROOT / 'plugin.json', root / 'plugin.json')
            with patch.object(plugin, 'ROOT', root):
                before = plugin.payload()[0]
                with (root / 'skills/plugin-manager/references/style.md').open('a') as handle:
                    handle.write('\nA revised documentation rule.\n')
                after = plugin.payload()[0]
                self.assertNotEqual(before, after)

    def test_isolated_plugin_scaffolds_without_developer_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize(root / 'installed')
            helper = root / 'installed/skills' / 'plugin-manager' / 'scripts/documentation.py'
            source = root / 'fictional'
            source.mkdir()
            (source / 'SKILL.md').write_text('---\nname: fictional\n---\n# Fictional skill')
            result = subprocess.run([sys.executable, str(helper), 'scaffold', '--source', str(source),
                                     '--output', str(root / 'docs-output'), '--languages', 'de', 'en'], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / 'docs-output/README.en.md').is_file())
            self.assertEqual((root / 'docs-output/docs/assets/zyris-icon.png').read_bytes(), (ROOT / 'assets/icon.png').read_bytes())


class RepositoryMetadataTests(unittest.TestCase):
    def test_committed_metadata_has_no_version_and_matches_identity(self):
        self.assertTrue(plugin.repository_metadata(check=True)['valid'])
        self.assertNotIn('version', plugin.configuration()[0])

    def test_sync_refuses_symlink_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ('skills', 'assets'):
                shutil.copytree(ROOT / folder, root / folder)
            shutil.copy2(ROOT / 'plugin.json', root / 'plugin.json')
            outside = root / 'outside'; outside.mkdir()
            (root / '.claude-plugin').symlink_to(outside, target_is_directory=True)
            with patch.object(plugin, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Symlink'):
                plugin.repository_metadata()
            self.assertEqual([], list(outside.iterdir()))
