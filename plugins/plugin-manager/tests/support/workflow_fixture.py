"""End-to-end creation/configuration using fictional repositories and isolated hosts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests.support.plugin_fixture import materialize

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
sys.path.insert(0, str(ROOT/'skills/_shared/scripts'))
import workflows as flow
import verify

class WorkflowFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.market = self.repo('market')
        flow.marketplace_create(self.market, 'fictional-market', 'Fictional Market', 'Fictional Publisher')
        self.source = self.root/'source'; self.source.mkdir()
        (self.source/'SKILL.md').write_text('---\nname: fictional-skill\ndescription: A fictional acceptance fixture.\n---\n# Fictional skill\nRepeat the supplied fictional greeting. Do not access personal data.\n')
        self.plugin = self.repo('new-plugin')


    def repo(self, name):
        path = self.root/name; path.mkdir()
        subprocess.run(['git','init','-q',str(path)],check=True)
        subprocess.run(['git','-C',str(path),'remote','add','origin','https://github.com/example/'+name+'.git'],check=True)
        return path


    def create(self, root=None, **licensing):
        return flow.plugin_create(root or self.plugin, self.market, skeleton=True, name=(root or self.plugin).name,
            display_name='Fictional Plugin', description='Fictional acceptance capability', author='Fictional Publisher', languages=['de','en'], default_language='de', **({'license':'deferred'} | licensing))


    def record(self, root=None):
        """Configuration evidence (schema 2) of the central entry, written only after a passed creation (record)."""
        root = root or self.plugin
        helper = flow.module(ROOT/'skills/_shared/scripts/project_setup.py', 'fixture_project_setup_' + root.name.replace('-', '_'))
        helper.set_plugin('plugin-manager')
        result = helper.record(str(root), 'plugin', root.name)
        assert result['ok'], result
        return result

    def create_configured(self, root=None, **licensing):
        result = self.create(root, **licensing)
        self.record(root)
        return result

    def make(self,root,action,host):
        args=['make','-s',action,'TARGET='+host,'DRY_RUN=1']
        return json.loads(subprocess.check_output(args,cwd=root,text=True))
