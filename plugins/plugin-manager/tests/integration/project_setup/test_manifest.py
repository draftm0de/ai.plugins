"""R16: kinds are described by sync/ and seed/ folders, a small manifest and the generated hash file."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests.support.project_setup_fixture import ROOT, SHARED, digest

TEMPLATES = SHARED / 'templates'
MANIFESTS = SHARED / 'manifests'
TOOL = ROOT / 'scripts/skeleton_hashes.py'
KINDS = ('marketplace', 'plugin')


def load(name):
    return json.loads((MANIFESTS / name).read_text(encoding='utf-8'))


def files_below(folder):
    return {str(p.relative_to(folder)): p for p in sorted(folder.rglob('*')) if p.is_file()}


class ManifestTests(unittest.TestCase):
    def test_every_kind_has_a_small_manifest_and_a_generated_sync_file(self):
        self.assertEqual(sorted([*(f'{k}.json' for k in KINDS), *(f'{k}.sync.json' for k in KINDS)]),
                         sorted(p.name for p in MANIFESTS.glob('*.json')))
        for kind in KINDS:
            with self.subTest(kind=kind):
                manifest = load(f'{kind}.json')
                self.assertEqual({'schema_version', 'product', 'requires_marketplace', 'derived'}, set(manifest))
                # R21: only a plugin belongs to a marketplace; a marketplace and a generated plugin's default kind do not
                self.assertEqual(kind == 'plugin', manifest['requires_marketplace'])
                sync = load(f'{kind}.sync.json')
                self.assertEqual({'schema_version', 'files', 'removed'}, set(sync))
                self.assertEqual(1, sync['schema_version'])
                self.assertFalse(set(sync['files']) & set(sync['removed']))
                self.assertEqual(sorted(sync['files']), list(sync['files']))
                self.assertEqual(sorted(sync['removed']), sync['removed'])

    def test_hash_file_matches_the_sync_folder_exactly_including_executable_bit(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                actual = files_below(TEMPLATES / kind / 'sync')
                listed = load(f'{kind}.sync.json')['files']
                self.assertEqual(set(actual), set(listed))
                for path, file in actual.items():
                    self.assertEqual({'sha256': digest(file.read_bytes()), 'executable': bool(file.stat().st_mode & 0o111)}, listed[path], path)

    def test_tombstones_are_removed_files_and_not_shipped(self):
        self.assertEqual(['install.sh', 'keep.md', 'remove.md'], load('plugin.sync.json')['removed'])
        self.assertEqual([], load('marketplace.sync.json')['removed'])
        for path in ('install.sh', 'keep.md', 'remove.md'):
            self.assertFalse((TEMPLATES / 'plugin/sync' / path).exists())
            self.assertFalse((TEMPLATES / 'plugin/seed' / path).exists())

    def test_check_tool_is_green_on_the_real_repository(self):
        result = subprocess.run([sys.executable, '-B', str(TOOL), 'check'], capture_output=True, text=True)
        self.assertEqual((0, 'skeleton hashes: ok\n'), (result.returncode, result.stdout), result.stderr)

    def test_a_file_is_either_synced_or_seeded_never_both(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.assertFalse(set(files_below(TEMPLATES / kind / 'sync')) & set(files_below(TEMPLATES / kind / 'seed')))
                self.assertEqual({'sync', 'seed'}, {p.name for p in (TEMPLATES / kind).iterdir()})

    def test_marketplace_classes_follow_the_scope(self):
        sync = load('marketplace.sync.json')
        self.assertEqual({'CLAUDE.md', 'scripts/local_plugins.py', 'scripts/marketplace.py', 'scripts/plugin_payload.py',
                          'scripts/run_tests.py', 'scripts/verify.py'}, set(sync['files']))
        seed = set(files_below(TEMPLATES / 'marketplace/seed'))
        self.assertEqual({'Makefile', 'AGENTS.md', 'SCOPE.md', 'docs/architecture.md', 'docs/prerequisites.md', 'local-marketplace.example.json',
                          'tests/README.md', 'tests/__init__.py', 'tests/contracts/__init__.py', 'tests/contracts/test_structure.py'}, seed)
        manifest = load('marketplace.json')
        self.assertEqual('marketplace.json', manifest['product'])
        self.assertEqual({'.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'}, {d['path'] for d in manifest['derived']})
        for derived in manifest['derived']:  # produced and checked by a synced script, never copied or hashed
            self.assertIn(derived['generate'].split()[2], sync['files'])
            self.assertNotIn(derived['path'], set(sync['files']) | seed)

    def test_plugin_classes_follow_the_scope(self):
        sync = set(load('plugin.sync.json')['files'])
        self.assertTrue({'CLAUDE.md', 'scripts/plugin.py', 'scripts/verify.py', 'scripts/run_tests.py',
                         'skills/_shared/scripts/operator_language.py', 'skills/_shared/references/operator-language.md', 'skills/_shared/scripts/messages_base.py', 'AGENTS.md',
                         'docs/standards/coding.md', 'docs/standards/messages.md', 'docs/standards/testing.md', 'docs/standards/skills.md'} == sync)  # R16: no setup flow; R27: the standards
        seed = set(files_below(TEMPLATES / 'plugin/seed'))
        self.assertTrue({'CUSTOM.AGENTS.md', 'SCOPE.md', 'assets/icon.png', 'Makefile', 'ci.yml', 'gitignore.txt', 'docs/architecture.md',
                         'docs/prerequisites.md', 'tests/README.md'} <= seed)
        self.assertEqual('plugin.json', load('plugin.json')['product'])

    def test_marketplace_makefile_is_minimal(self):
        text = (TEMPLATES / 'marketplace/seed/Makefile').read_text()
        for target in ('install-local:', 'test:'):
            self.assertIn(target, text)
        for gone in ('update-local', 'plugin-verify', 'marketplace-verify', 'plugin-create', 'marketplace-create', 'configure'):
            self.assertNotIn(gone, text)

    def test_claude_file_is_identical_for_every_kind_and_only_imports_agents_md(self):
        contents = {(TEMPLATES / kind / 'sync/CLAUDE.md').read_text() for kind in KINDS}
        self.assertEqual(1, len(contents))
        self.assertEqual(['@AGENTS.md'], [line for line in contents.pop().splitlines() if line.startswith('@')])

    def test_the_managed_agents_file_imports_the_plugin_own_file_and_the_standards(self):  # R27, R28
        imports = [line for line in (TEMPLATES / 'plugin/sync/AGENTS.md').read_text().splitlines() if line.startswith('@')]
        self.assertEqual(['@CUSTOM.AGENTS.md'] + ['@docs/standards/' + n for n in ('coding.md', 'messages.md', 'testing.md', 'skills.md')], imports)

    def test_line_endings_never_change_a_hash(self):
        self.assertEqual('* -text', (TEMPLATES / '.gitattributes').read_text().strip())
        self.assertEqual('*.sync.json -text', (MANIFESTS / '.gitattributes').read_text().strip())


if __name__ == '__main__':
    unittest.main()
