import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
ROOT=next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
spec=importlib.util.spec_from_file_location('local_plugins', ROOT/'scripts/local_plugins.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class SharedLocalTestsFixture:
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'market';self.root.mkdir()
        (self.root/'scripts').mkdir()
        shutil.copy2(ROOT/'scripts/marketplace.py',self.root/'scripts/marketplace.py')
        self.manager=self.root.parent/'manager';self.coach=self.root.parent/'coach'
        for path,name in ((self.manager,'plugin-manager'),(self.coach,'interview-coach')):
            (path/'skills/example').mkdir(parents=True)
            (path/'skills/example/SKILL.md').write_text('---\nname: example\ndescription: Fictional test.\n---\n# Example\n')
            (path/'plugin.json').write_text(json.dumps({'name':name,'description':'Fictional test','repository':'https://github.com/example/coach','extensions':{'io.zyris.distribution':{'skillRoot':'skills','catalogs':False}}}))
        (self.manager/'scripts').mkdir()
        shutil.copy2(ROOT/'plugins/plugin-manager/scripts/plugin.py',self.manager/'scripts/plugin.py')
        config={'name':'shared-fixture','displayName':'Shared Fixture','owner':{'name':'Fixture'},'plugins':[{'name':'plugin-manager','displayName':'Plugin Manager','description':'Fictional test','repository':'https://github.com/example/coach.git'},{'name':'interview-coach','displayName':'Interview Coach','description':'Fictional test','repository':'https://github.com/example/coach.git'}]}
        (self.root/'marketplace.json').write_text(json.dumps(config))
        (self.root/'.local').mkdir()
        (self.root/'.local/marketplace.json').write_text(json.dumps({'sources':{'interview-coach':str(self.coach),'plugin-manager':str(self.manager)}}))
