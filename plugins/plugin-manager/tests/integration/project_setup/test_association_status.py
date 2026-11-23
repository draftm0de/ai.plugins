"""R21: status reports the read-only association of a plugin; it never gates ready and never writes."""
import json
from pathlib import Path
import unittest

from tests.support.project_setup_fixture import Sandbox, tree

LOCAL = '.project/plugins/plugin-manager/local.json'
REPO = 'https://github.com/fictional/demo-plugin'
IDENTITY = {'name': 'fictional-market'}  # the identity of a marketplace is its name


class AssociationStatusTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox().make(); self.addCleanup(self.box.close)
        self.p = self.box.project
        (self.p / 'plugin.json').write_text(json.dumps({'name': 'demo-plugin', 'repository': REPO + '.git'}))
        self.assertEqual(0, self.box.call('language', '--language', 'de')[0])
        self.assertEqual(0, self.box.call('setup')[0])
        self.market = self.p.parent / 'market'

    def status(self):
        code, data, _ = self.box.call('status')
        self.assertEqual(0, code)
        return data

    def local(self, value):
        path = self.p / LOCAL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))

    def point(self, value='../market'):
        self.local({'schema_version': 1, 'marketplace_path': value})

    def catalog(self, plugins=None, **identity):
        self.market.mkdir(exist_ok=True)
        config = dict(IDENTITY, **identity)
        config['plugins'] = [{'name': 'demo-plugin', 'repository': REPO + '.git'}] if plugins is None else plugins
        (self.market / 'marketplace.json').write_text(json.dumps(config))

    def test_the_identity_is_part_of_the_configuration_and_path_missing_is_only_a_hint(self):
        data = self.status()
        self.assertEqual({'marketplace': IDENTITY, 'path': None, 'state': 'path_missing'}, data['association'])
        self.assertEqual(('ready', True), (data['next'], data['configuration']['configured']))  # a fresh clone is still configured

    def test_ok_when_the_checkout_exists_and_lists_the_plugin(self):
        self.catalog(); self.point()
        data = self.status()
        self.assertEqual(({'marketplace': IDENTITY, 'path': '../market', 'state': 'ok'}, 'ready'), (data['association'], data['next']))

    def test_absolute_path_is_resolved_too(self):
        self.catalog(); self.point(str(self.market))
        self.assertEqual('ok', self.status()['association']['state'])

    def test_path_invalid_when_the_target_is_gone_or_no_marketplace(self):
        self.point('../gone')
        self.assertEqual({'marketplace': IDENTITY, 'path': '../gone', 'state': 'path_invalid'}, self.status()['association'])
        self.market.mkdir()
        self.point()
        self.assertEqual('path_invalid', self.status()['association']['state'])  # a folder without marketplace.json
        (self.market / 'marketplace.json').write_text('{not json')
        self.assertEqual('path_invalid', self.status()['association']['state'])

    def test_mismatch_when_the_checkout_or_its_catalog_entry_does_not_fit_the_identity(self):
        self.point()
        cases = {'another marketplace name': dict(name='other-market'),
                 'plugin not listed': dict(plugins=[]),
                 'plugin listed for another repository': dict(plugins=[{'name': 'demo-plugin', 'repository': 'https://github.com/x/y.git'}])}
        for label, change in cases.items():
            with self.subTest(label):
                self.catalog(**change)
                data = self.status()
                self.assertEqual(('mismatch', 'ready', True), (data['association']['state'], data['next'], data['ok']))  # a hint, never a gate

    def test_plugin_repository_urls_compare_without_dot_git_and_case(self):
        self.point()
        self.catalog(plugins=[{'name': 'demo-plugin', 'repository': REPO.upper().replace('HTTPS', 'https')}])
        self.assertEqual('ok', self.status()['association']['state'])

    def test_unsupported_local_formats_are_a_hint_not_a_conflict(self):
        for value in ({'marketplace': '../market'}, {'schema_version': 1, 'marketplace_path': '../a', 'marketplaces': {}},
                      {'schema_version': 2, 'marketplace_path': '../a'}, {'schema_version': 1, 'marketplace_path': 5},
                      {'schema_version': 1, 'marketplace_path': ' '}, '{not json', '[]'):
            with self.subTest(value=value):
                self.local(value)
                data = self.status()
                self.assertEqual(('unsupported', 'ready', True), (data['association']['state'], data['next'], data['ok']))

    def test_the_former_plugin_side_file_is_not_looked_at(self):
        legacy = self.p / '.local/marketplace.json'
        legacy.parent.mkdir()
        legacy.write_text(json.dumps({'marketplace': '../market'}))
        self.assertEqual('path_missing', self.status()['association']['state'])

    def test_status_never_writes_and_a_marketplace_has_no_association(self):
        self.catalog(); self.point()
        before = tree(self.p)
        self.status()
        self.assertEqual(before, tree(self.p))
        self.box.configure('demo-market', 'marketplace')
        (self.p / 'plugin.json').unlink()
        (self.p / 'marketplace.json').write_text(json.dumps({'name': 'demo-market'}))
        code, data, _ = self.box.call('status')
        self.assertEqual((0, None), (code, data['association']))

    def test_record_requires_the_association_and_writes_its_identity(self):
        self.box.unconfigure()
        (self.p / 'plugin.json').write_text(json.dumps({'name': 'demo-plugin', 'repository': REPO + '.git'}))
        before = tree(self.p)
        for label, prepare in (('no local path', lambda: None), ('unsupported file', lambda: self.local({'marketplace': '../market'})),
                               ('plugin not listed', lambda: (self.point(), self.catalog(plugins=[])))):
            with self.subTest(label):
                prepare()
                code, data, _ = self.box.call('record', '--kind', 'plugin', '--artifact', 'demo-plugin')
                self.assertEqual((1, 'association_missing'), (code, data['conflicts'][0]['code']))
                self.assertIn('associate first', data['conflicts'][0]['reason'])
                self.assertFalse((self.p / '.project/plugins/plugin-manager/config.json').exists())
        self.catalog(); self.point()
        code, data, _ = self.box.call('record', '--kind', 'plugin', '--artifact', 'demo-plugin')
        self.assertEqual((0, True), (code, data['ok']))
        written = json.loads((self.p / '.project/plugins/plugin-manager/config.json').read_text())
        self.assertEqual((2, IDENTITY), (written['schema_version'], written['marketplace']))
        self.assertEqual('ok', self.status()['association']['state'])

    def test_record_of_a_marketplace_stores_no_association(self):
        self.box.unconfigure()
        (self.p / 'marketplace.json').write_text(json.dumps({'name': 'demo-market'}))
        code, data, _ = self.box.call('record', '--kind', 'marketplace', '--artifact', 'demo-market')
        self.assertEqual((0, True), (code, data['ok']))
        self.assertIsNone(json.loads((self.p / '.project/plugins/plugin-manager/config.json').read_text())['marketplace'])


if __name__ == '__main__':
    unittest.main()
