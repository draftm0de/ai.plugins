"""R15/R21: the identity of a marketplace is its name; plugin creation checks it before it writes anything."""
import json
import subprocess
import unittest

from tests.support.workflow_fixture import WorkflowFixture, flow


def snapshot(*roots):
    return {str(p): p.read_bytes() for base in roots for p in sorted(base.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(base).parts}


class MarketplaceIdentityTests(WorkflowFixture, unittest.TestCase):
    def test_a_marketplace_without_origin_and_repository_works(self):
        local = self.root / 'local-market'
        local.mkdir()
        subprocess.run(['git', 'init', '-q', str(local)], check=True)  # a Git repository, but no origin
        flow.create_marketplace(local, 'local-market', 'Local Market', 'Fictional Publisher')
        self.assertNotIn('repository', json.loads((local / 'marketplace.json').read_text()))
        self.market = local
        self.create_configured()
        self.assertEqual({'name': 'local-market'}, json.loads((self.plugin / '.project/plugins/plugin-manager/config.json').read_text())['marketplace'])

    def test_a_marketplace_that_is_not_a_git_repository_is_refused(self):
        plain = self.root / 'plain'
        plain.mkdir()
        with self.assertRaises(Exception):
            flow.create_marketplace(plain, 'plain', 'Plain', 'Fictional Publisher')

    def test_a_marketplace_without_a_name_is_refused_before_any_write(self):
        config = json.loads((self.market / 'marketplace.json').read_text())
        del config['name']
        (self.market / 'marketplace.json').write_text(json.dumps(config, indent=2) + '\n')
        before = snapshot(self.plugin, self.market)
        with self.assertRaises(ValueError):
            self.create()
        self.assertEqual(before, snapshot(self.plugin, self.market))  # nothing in the plugin, nothing in the marketplace


if __name__ == '__main__':
    unittest.main()
