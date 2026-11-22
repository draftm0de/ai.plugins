"""R21: the associate operation - a plugin belongs to exactly one marketplace; fictional repositories only.

The identity of the marketplace is part of the committed config.json, the path of its checkout lives in the ignored
.project/plugins/plugin-manager/local.json."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests.support.workflow_fixture import WorkflowFixture, flow, ROOT

LOCAL = '.project/plugins/plugin-manager/local.json'
CONFIG = '.project/plugins/plugin-manager/config.json'


def snapshot(*roots):
    return {str(p): p.read_bytes() for base in roots for p in sorted(base.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(base).parts}


class AssociateBase(WorkflowFixture, unittest.TestCase):
    def second_market(self, name='second-market'):
        path = self.repo(name)
        flow.create_marketplace(path, name, 'Second Fictional Market', 'Fictional Publisher')
        return path

    def configured(self):
        self.create_configured()

    def local(self, plugin=None):
        return json.loads(((plugin or self.plugin) / LOCAL).read_text())

    def config(self, plugin=None):
        return json.loads(((plugin or self.plugin) / CONFIG).read_text())


class AssociateTests(AssociateBase):
    def test_creation_binds_one_marketplace_identity_and_local_path(self):
        self.configured()
        self.assertEqual({'schema_version': 1, 'marketplace_path': os.path.relpath(self.market, self.plugin)}, self.local())
        config = self.config()
        self.assertEqual(2, config['schema_version'])
        self.assertEqual({'name': 'fictional-market', 'repository': 'https://github.com/example/market'},
                         {'name': config['marketplace']['name'], 'repository': config['marketplace']['repository'].removesuffix('.git')})
        self.assertFalse((self.plugin / '.local/marketplace.json').exists())  # the plugin-side .local file is gone

    def test_association_with_the_same_marketplace_is_idempotent(self):
        self.configured()
        before = snapshot(self.plugin, self.market)
        result = flow.associate(self.plugin, self.market)
        self.assertEqual(([], False, False), (result['changed'], result['published'], result['old_catalog_entry_remains']))
        self.assertEqual(('fictional-market', 'fictional-market'), (result['from']['name'], result['to']['name']))
        self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_fresh_clone_writes_only_the_local_path_and_no_tools(self):
        self.configured()
        (self.plugin / LOCAL).unlink()
        before_config = (self.plugin / CONFIG).read_bytes()
        (self.plugin / 'Makefile').write_text('custom-check:\n\t@echo preserved\n')
        result = flow.associate(self.plugin, self.market)
        self.assertEqual([str(self.plugin / LOCAL)], [c for c in result['changed'] if c.endswith('local.json')])
        self.assertEqual(before_config, (self.plugin / CONFIG).read_bytes())  # identity is already committed
        self.assertEqual('custom-check:\n\t@echo preserved\n', (self.plugin / 'Makefile').read_text())  # no tools are written
        self.assertEqual(os.path.relpath(self.market, self.plugin), self.local()['marketplace_path'])

    def test_moved_checkout_of_the_same_marketplace_only_updates_the_path(self):
        self.configured()
        moved = self.root / 'moved-market'
        shutil.copytree(self.market, moved)
        shutil.rmtree(self.market)
        before_config = (self.plugin / CONFIG).read_bytes()
        result = flow.associate(self.plugin, moved)
        self.assertFalse(result['old_catalog_entry_remains'])
        self.assertEqual(os.path.relpath(moved, self.plugin), self.local()['marketplace_path'])
        self.assertEqual(before_config, (self.plugin / CONFIG).read_bytes())

    def test_change_moves_the_association_in_one_step(self):
        self.configured()
        second = self.second_market()
        result = flow.associate(self.plugin, second)
        self.assertEqual(('fictional-market', 'second-market', False, False),
                         (result['from']['name'], result['to']['name'], result['published'], result['old_catalog_entry_remains']))
        self.assertIn('publish', result['next'])
        self.assertIn('config.json', result['next'])  # committed files changed: the person has to know
        self.assertEqual({'schema_version': 1, 'marketplace_path': os.path.relpath(second, self.plugin)}, self.local())
        self.assertEqual('second-market', self.config()['marketplace']['name'])
        old = json.loads((self.market / 'marketplace.json').read_text())
        new = json.loads((second / 'marketplace.json').read_text())
        self.assertEqual([], [e for e in old['plugins'] if e['name'] == 'new-plugin'])
        self.assertEqual(['new-plugin'], [e['name'] for e in new['plugins']])
        self.assertNotIn('new-plugin', json.loads((self.market / '.local/marketplace.json').read_text()).get('sources', {}))
        self.assertEqual(os.path.relpath(self.plugin, second), json.loads((second / '.local/marketplace.json').read_text())['sources']['new-plugin'])
        for market, config in ((self.market, old), (second, new)):  # both host catalogs of both marketplaces are regenerated
            for path, data in flow.catalog_files(market, config).items():
                self.assertEqual(data, path.read_bytes(), str(path))
        self.assertEqual('second-market-dev', self.make(self.plugin, 'install-local', 'codex')['marketplace'])

    def test_install_local_has_no_marketplace_override(self):  # R21
        self.configured()
        second = self.second_market()
        script = self.plugin / 'scripts/plugin.py'
        run = subprocess.run([sys.executable, '-B', str(script), 'install-local', '--target', 'codex', '--dry-run',
                              '--marketplace', str(second)], capture_output=True, text=True, cwd=self.plugin)
        self.assertEqual(2, run.returncode)  # invalid invocation, no such option
        self.assertIn('--marketplace', run.stderr)
        # the former make variable is ignored: the marketplace comes only from local.json
        out = json.loads(subprocess.check_output(['make', '-s', 'install-local', 'TARGET=codex', 'DRY_RUN=1',
                                                  'MARKETPLACE=' + str(second)], cwd=self.plugin, text=True))
        self.assertEqual('fictional-market-dev', out['marketplace'])
        self.assertNotIn('MARKETPLACE', (self.plugin / 'Makefile').read_text())
        for relative in ('scripts/plugin.py', 'scripts/plugin_payload.py'):
            path = ROOT.parent.parent / relative if relative == 'scripts/plugin_payload.py' else self.plugin / relative
            self.assertNotIn('marketplace_root', path.read_text(), relative)
            self.assertNotIn('pass --marketplace PATH', path.read_text(), relative)

    def test_failed_write_rolls_back_all_three_repositories(self):
        self.configured()
        second = self.second_market()
        before = snapshot(self.plugin, self.market, second)
        real, calls = os.replace, {'n': 0}
        def failing(source, destination):
            calls['n'] += 1
            if calls['n'] > 3:
                raise OSError('forced failure')
            return real(source, destination)
        with patch.object(flow.os, 'replace', side_effect=failing):
            with self.assertRaises(OSError):
                flow.associate(self.plugin, second)
        self.assertGreater(calls['n'], 3)
        self.assertEqual(before, snapshot(self.plugin, self.market, second))  # config.json and local.json included

    def test_missing_old_marketplace_is_refused_unless_dropped_explicitly(self):
        self.configured()
        second = self.second_market()
        shutil.rmtree(self.market)
        before = snapshot(self.plugin, second)
        with self.assertRaisesRegex(ValueError, 'drop-missing-old'):
            flow.associate(self.plugin, second)
        self.assertEqual(before, snapshot(self.plugin, second))
        result = flow.associate(self.plugin, second, drop_missing_old=True)
        self.assertTrue(result['old_catalog_entry_remains'])
        self.assertEqual('second-market', self.config()['marketplace']['name'])
        self.assertEqual(os.path.relpath(second, self.plugin), self.local()['marketplace_path'])
        self.assertEqual(['new-plugin'], [e['name'] for e in json.loads((second / 'marketplace.json').read_text())['plugins']])

    def test_old_catalog_entry_of_a_different_repository_blocks_the_change(self):
        self.configured()
        second = self.second_market()
        config = json.loads((self.market / 'marketplace.json').read_text())
        config['plugins'][0]['repository'] = 'https://github.com/example/another-repo.git'
        (self.market / 'marketplace.json').write_bytes(flow.encode(config))
        before = snapshot(self.plugin, self.market, second)
        with self.assertRaises(ValueError):
            flow.associate(self.plugin, second)
        self.assertEqual(before, snapshot(self.plugin, self.market, second))

    def test_same_marketplace_name_with_another_repository_is_an_identity_conflict(self):
        self.configured()
        impostor = self.repo('impostor')
        flow.create_marketplace(impostor, 'fictional-market', 'Fictional Market', 'Fictional Publisher')
        before = snapshot(self.plugin, self.market, impostor)
        with self.assertRaisesRegex(ValueError, 'Marketplace identity conflicts'):
            flow.associate(self.plugin, impostor)
        self.assertEqual(before, snapshot(self.plugin, self.market, impostor))

    def test_target_must_be_a_marketplace_and_separate_from_the_plugin(self):
        self.configured()
        plain = self.repo('plain-repo')
        self.create_configured(self.repo('other-plugin'))
        for target in (plain, self.root / 'other-plugin', self.plugin, self.plugin / 'nested'):
            with self.subTest(target=target.name):
                before = snapshot(self.plugin, self.market)
                with self.assertRaises((ValueError, OSError, subprocess.CalledProcessError)):
                    flow.associate(self.plugin, target)
                self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_tracked_local_configuration_blocks_the_change(self):
        self.configured()
        second = self.second_market()
        (second / '.local').mkdir(exist_ok=True)
        (second / '.local/marketplace.json').write_text('{"sources": {}}\n')
        subprocess.run(['git', '-C', str(second), 'add', '-f', '.local/marketplace.json'], check=True)
        before = snapshot(self.plugin, self.market, second)
        with self.assertRaisesRegex(ValueError, 'tracked'):
            flow.associate(self.plugin, second)
        self.assertEqual(before, snapshot(self.plugin, self.market, second))
        subprocess.run(['git', '-C', str(second), 'rm', '-q', '--cached', '.local/marketplace.json'], check=True)
        subprocess.run(['git', '-C', str(self.plugin), 'add', '-f', LOCAL], check=True)  # the machine path must never be committed
        with self.assertRaisesRegex(ValueError, 'tracked'):
            flow.associate(self.plugin, second)

    def test_unsupported_local_formats_are_refused_and_never_migrated(self):
        self.configured()
        second = self.second_market()
        for content in ({'marketplace': '../market'}, {'schema_version': 1, 'marketplace_path': '../m', 'marketplaces': {}},
                        {'schema_version': 2, 'marketplace_path': '../m'}, {'schema_version': 1, 'marketplace_path': 5}):
            with self.subTest(content=content):
                (self.plugin / LOCAL).write_bytes(flow.encode(content))
                before = snapshot(self.plugin, self.market, second)
                with self.assertRaisesRegex(ValueError, 'Unsupported plugin-local association format'):
                    flow.associate(self.plugin, second)
                self.assertEqual(before, snapshot(self.plugin, self.market, second))

    def test_former_plugin_side_local_file_is_not_read_and_not_touched(self):
        self.configured()
        legacy = self.plugin / '.local/marketplace.json'
        legacy.parent.mkdir(exist_ok=True)
        legacy.write_text('{"marketplaces": {"x": "../x"}, "marketplace": "../x"}')
        flow.associate(self.plugin, self.market)  # not read: the unsupported old content neither blocks nor is migrated
        self.assertEqual('{"marketplaces": {"x": "../x"}, "marketplace": "../x"}', legacy.read_text())

    def test_requires_the_configuration_evidence_of_a_plugin(self):
        self.create()  # created but never recorded: no config.json yet
        with self.assertRaisesRegex(ValueError, 'Configure first'):
            flow.associate(self.plugin, self.market)
        self.record()
        config = self.config()
        config['schema_version'] = 1
        del config['marketplace']
        (self.plugin / CONFIG).write_bytes(flow.encode(config))
        before = snapshot(self.plugin, self.market)
        with self.assertRaisesRegex(ValueError, 'Unsupported configuration evidence'):
            flow.associate(self.plugin, self.market)
        self.assertEqual(before, snapshot(self.plugin, self.market))

    def test_local_json_is_ignored_for_the_plugin_only(self):
        self.configured()
        self.assertIn('/.project/plugins/*/local.json', (self.plugin / '.gitignore').read_text().splitlines())
        self.assertNotIn('/.project/plugins/*/local.json', (self.market / '.gitignore').read_text().splitlines())
        ignored = subprocess.run(['git', '-C', str(self.plugin), 'check-ignore', '-q', LOCAL])
        self.assertEqual(0, ignored.returncode)
        self.assertNotEqual(0, subprocess.run(['git', '-C', str(self.plugin), 'check-ignore', '-q', CONFIG]).returncode)  # config is committed

    def test_runtime_reads_local_json_and_has_no_fallback(self):
        self.configured()
        engine = [sys.executable, '-B', str(self.plugin / 'scripts/plugin.py'), 'install-local', '--target', 'codex', '--dry-run']
        self.assertEqual(0, subprocess.run(engine, cwd=self.plugin, capture_output=True, text=True).returncode)
        (self.plugin / LOCAL).unlink()
        legacy = self.plugin / '.local/marketplace.json'
        legacy.parent.mkdir(exist_ok=True)
        legacy.write_text(json.dumps({'marketplace': os.path.relpath(self.market, self.plugin)}))
        run = subprocess.run(engine, cwd=self.plugin, capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)  # the former file is no fallback
        self.assertIn('plugin-manager (associate)', run.stderr)

    def test_cli_has_associate_and_no_configure(self):
        self.configured()
        second = self.second_market()
        script = str(ROOT / 'skills/_shared/scripts/workflows.py')
        run = subprocess.run([sys.executable, '-B', script, 'associate', '--root', str(self.plugin), '--marketplace', str(second)],
                             capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual(('associate', False), (json.loads(run.stdout)['action'], json.loads(run.stdout)['published']))
        old = subprocess.run([sys.executable, '-B', script, 'configure', '--root', str(self.plugin), '--marketplace', str(second)],
                             capture_output=True, text=True)
        self.assertEqual(2, old.returncode)  # the former operation is gone, no alias
        self.assertFalse(hasattr(flow, 'configure'))

    def test_runtime_messages_name_the_associate_flow_not_configure(self):
        for relative in ('scripts/plugin_payload.py', 'scripts/verify.py'):
            text = (ROOT.parent.parent / relative).read_text()
            self.assertNotIn('run configure', text)
        self.assertIn('plugin-manager (associate)', (ROOT.parent.parent / 'scripts/plugin_payload.py').read_text())


if __name__ == '__main__':
    unittest.main()
