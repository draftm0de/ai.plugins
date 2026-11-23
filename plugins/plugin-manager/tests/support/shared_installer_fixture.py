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
from tests.support.marketplace_fixture import attach

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
if not (ROOT / 'plugin.json').is_file():
    ROOT = ROOT.parent
spec = importlib.util.spec_from_file_location('shared_installer', ROOT / 'scripts/plugin.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class SharedInstallerTestsFixture:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()/'plugin'
        self.root.mkdir()
        source = self.root / 'skills/fictional-skill'
        source.mkdir(parents=True)
        (source / 'SKILL.md').write_text('---\nname: fictional-skill\ndescription: Fictional test\n---\n# Test')
        self.manifest = {'name':'fictional-product', 'repository':'https://github.com/example/fictional-product','description':'Fictional plugin',
            'extensions': {'io.zyris.distribution':{'skillRoot':'skills'}}}
        self.write_manifest()
        self.market = attach(self.root)
        with patch.object(engine, 'ROOT', self.root): engine.repository_metadata()
        for relative in ('scripts/plugin.py',):
            target = self.root / relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT / relative,target)
        (self.root / 'Makefile').write_text('PYTHON ?= python3\nTARGET ?= claude\nDRY_RUN ?= 0\n' + (ROOT/'Makefile').read_text().split('# Local development and repository metadata', 1)[1])


    def write_manifest(self):
        (self.root / 'plugin.json').write_text(json.dumps(self.manifest))


    def invoke(self, *args):
        return subprocess.run(args,cwd=self.root,capture_output=True,text=True,check=True)


class LocalDevelopmentTestsFixture:
    setUp = SharedInstallerTestsFixture.setUp


    write_manifest = SharedInstallerTestsFixture.write_manifest
