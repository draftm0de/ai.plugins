"""Packaging rules of scripts/plugin_payload.py. Managed by plugin-manager; fictional data only."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('plugin_payload', ROOT / 'scripts/plugin_payload.py')
payload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload_module)


class PluginPayloadTests(unittest.TestCase):
    def test_only_named_template_dot_files_are_packaged_and_private_files_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            files = {'SKILL.md': '---\nname: example\ndescription: Fictional.\n---\n# Example\n',
                     'templates/site/.gitignore.tpl': 'dist/\n', 'templates/site/public/.gitkeep': '',
                     'templates/site/.secret': 'x', 'templates/site/.hidden/inner.txt': 'x',
                     'templates/site/.gitignore': 'x', 'other/.gitignore.tpl': 'x', 'templates/site/.env.tpl': 'x',
                     'templates/site/sync/.github/workflows/ci.yml': 'x', 'templates/site/sync/.github/other.yml': 'x',
                     'templates/site/.github/workflows/ci.yml': 'x', 'other/sync/.github/workflows/ci.yml': 'x'}
            for relative, text in files.items():
                path = root / 'skills/example' / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            (root / 'plugin.json').write_text(json.dumps({'name': 'fictional', 'description': 'Fictional',
                'extensions': {'io.zyris.distribution': {'skillRoot': 'skills', 'catalogs': False}}}))
            previous = payload_module.ROOT
            self.addCleanup(setattr, payload_module, 'ROOT', previous)
            payload_module.ROOT = root
            with self.assertRaisesRegex(ValueError, 'Private file'):    # refused, not skipped
                payload_module.payload()
            (root / 'skills/example/templates/site/.env.tpl').unlink()
            names = set(payload_module.payload()[2])
            self.assertIn('skills/example/templates/site/.gitignore.tpl', names)
            self.assertIn('skills/example/templates/site/public/.gitkeep', names)
            self.assertIn('skills/example/templates/site/sync/.github/workflows/ci.yml', names)
            for blocked in ('templates/site/sync/.github/other.yml', 'templates/site/.github/workflows/ci.yml',
                            'other/sync/.github/workflows/ci.yml', 'templates/site/.secret', 'templates/site/.hidden/inner.txt',
                            'templates/site/.gitignore', 'other/.gitignore.tpl'):
                self.assertNotIn('skills/example/' + blocked, names)


if __name__ == '__main__':
    unittest.main()
