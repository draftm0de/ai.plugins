import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
spec = importlib.util.spec_from_file_location('plugin_payload', ROOT / 'scripts/plugin_payload.py')
payload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload_module)


class DotResourcePackagingTests(unittest.TestCase):
    def test_only_named_template_dot_files_are_packaged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            skill = root / 'skills/example'
            files = {
                'SKILL.md': '---\nname: example\ndescription: Fictional.\n---\n# Example\n',
                'templates/site/.gitignore.tpl': 'dist/\n',
                'templates/site/public/.gitkeep': '',
                'templates/site/.secret': 'x',
                'templates/site/.hidden/inner.txt': 'x',
                'templates/site/.gitignore': 'x',
                'other/.gitignore.tpl': 'x',
                'templates/site/.env.tpl': 'x',
            }
            for rel, text in files.items():
                path = skill / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            (root / 'plugin.json').write_text(json.dumps({'name': 'fixture', 'description': 'Fictional', 'extensions': {'io.zyris.distribution': {'skillRoot': 'skills', 'catalogs': False}}}))
            payload_module.ROOT = root
            with self.assertRaisesRegex(ValueError, 'Private file'):    # the .env.tpl template must be refused, not skipped
                payload_module.payload()
            (skill / 'templates/site/.env.tpl').unlink()
            _version, _portable, claude = payload_module.payload()
            names = set(claude)
            self.assertIn('skills/example/templates/site/.gitignore.tpl', names)
            self.assertIn('skills/example/templates/site/public/.gitkeep', names)
            for blocked in ('.secret', '.hidden/inner.txt', '.gitignore'):
                self.assertNotIn('skills/example/templates/site/' + blocked, names)
            self.assertNotIn('skills/example/other/.gitignore.tpl', names)


if __name__ == '__main__':
    unittest.main()
