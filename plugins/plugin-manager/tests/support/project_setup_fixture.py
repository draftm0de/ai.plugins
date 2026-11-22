"""Helpers for project-setup tests: fictional temporary plugins and isolated Manager copies."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
SHARED = ROOT / 'skills/_shared'
TEMPLATE_DIR = SHARED / 'templates/plugin'
# Files of the real skeleton whose delivery the delivery/integration tests check. keep.md and remove.md (manual
# sync-test sources) are deliberately not listed: they may disappear from the real parent. Rule tests of the sync
# do not use this list at all; they use FictionalSandbox with fixed fictional bytes (see tests/README.md).
FILES = ('CLAUDE.md', 'scripts/plugin.py', 'scripts/verify.py', 'scripts/run_tests.py', 'install.sh',
         'skills/_shared/scripts/operator_language.py', 'skills/_shared/references/operator-language.md')
LOCK = '.project/plugin.skeleton.lock.json'


def template(relative):
    return (SHARED / 'templates/plugin' / relative).read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pair(data, local=None):
    """Lock entry for template bytes `data` and local bytes `local` (default: identical)."""
    return {'source_hash': digest(data), 'local_hash': digest(data if local is None else local)}


def raw_pair(source_hash, local_hash=None):
    return {'source_hash': source_hash, 'local_hash': local_hash or source_hash}


def tree(path):
    """Relative path -> (bytes or None, mode) for before/after comparison."""
    path = Path(path)
    def content(p):
        try:
            if p.is_symlink():
                return b'->' + os.readlink(p).encode()
            return None if p.is_dir() else p.read_bytes()
        except PermissionError:
            return b'<unreadable>'
    return {str(p.relative_to(path)): (content(p), p.stat().st_mode) for p in sorted(path.rglob('*'))}


class Sandbox:
    def make(self, name='demo-plugin'):
        """Complete isolated copy of the real Manager's shared tree: delivery/integration tests only."""
        self.temp = tempfile.TemporaryDirectory(prefix='project setup ')
        self.base = Path(self.temp.name).resolve()
        self.manager = self.base / 'manager copy'
        shutil.copytree(SHARED, self.manager / 'skills/_shared', ignore=shutil.ignore_patterns('__pycache__'))
        self.helper = self.manager / 'skills/_shared/scripts/project_setup.py'
        self.project = self.base / 'my plugin'
        self.project.mkdir()
        (self.project / 'plugin.json').write_text(json.dumps({'name': name}))
        return self

    def close(self):
        for path in self.base.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
            elif path.is_file():
                path.chmod(0o644)
        self.temp.cleanup()

    def template(self, relative):
        return (self.manager / 'skills/_shared/templates/plugin' / relative).read_bytes()

    def run(self, operation, *args, target=None, helper=None):
        command = [sys.executable, '-B', '-I', str(helper or self.helper), operation, '--target',
                   str(target or self.project), *args]
        return subprocess.run(command, capture_output=True, text=True, cwd=self.base, env={'PATH': ''})

    def call(self, operation, *args, **kw):
        result = self.run(operation, *args, **kw)
        return result.returncode, (json.loads(result.stdout) if result.stdout else None), result

    def lock(self):
        return json.loads((self.project / LOCK).read_text())['files']


# ---- Minimal fictional parent for the sync/removal rule tests --------------------------------------------------
# Fixed, test-defined contents. Expectations are computed from these literals with hashlib, never from the real
# templates or from the real MANAGED_FILES.
ALPHA = b'# alpha v1\n'
BETA = b'beta v1\n'
ZETA = b'zeta v1\n'
GAMMA = b'#!/bin/sh\necho gamma v1\n'
DELTA = b'# delta v1\n'
FICTIONAL = {  # path -> (bytes, executable)
    'alpha.md': (ALPHA, False),
    'delta.md': (DELTA, False),
    'docs/beta.txt': (BETA, False),
    'docs/zeta.txt': (ZETA, False),
    'tools/deep/gamma.sh': (GAMMA, True),
}


class FictionalSandbox(Sandbox):
    """Runs the REAL project_setup.py (and the real operator_language.py it depends on) against a minimal fictional
    parent. Only the module constants MANAGED_FILES/FRESH_ENTRIES of the copied script are set to the fictional
    list; no function of the helper is replaced."""

    def make(self, name='demo-plugin', files=None):
        self.files = dict(FICTIONAL if files is None else files)
        self.temp = tempfile.TemporaryDirectory(prefix='project setup fiction ')
        self.base = Path(self.temp.name).resolve()
        self.manager = self.base / 'fictional parent'
        scripts = self.manager / 'skills/_shared/scripts'
        scripts.mkdir(parents=True)
        shutil.copy2(SHARED / 'scripts/operator_language.py', scripts / 'operator_language.py')
        source = (SHARED / 'scripts/project_setup.py').read_text()
        import re
        tops = ('.git', '.idea', '.gitignore', '.project') + tuple(dict.fromkeys(path.split('/')[0] for path in self.files))
        source, count_a = re.subn(r'MANAGED_FILES = \(.*?\n\)\n', lambda _: 'MANAGED_FILES = ' + repr(tuple(self.files)) + '\n', source, count=1, flags=re.S)
        source, count_b = re.subn(r'FRESH_ENTRIES = \(.*?\)\n', lambda _: 'FRESH_ENTRIES = ' + repr(tops) + '\n', source, count=1)
        assert (count_a, count_b) == (1, 1), 'constants of project_setup.py not found'
        self.helper = scripts / 'project_setup.py'
        self.helper.write_text(source)
        for path, (data, executable) in self.files.items():
            target = self.manager / 'skills/_shared/templates/plugin' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if executable else 0o644)
        self.project = self.base / 'my plugin'
        self.project.mkdir()
        (self.project / 'plugin.json').write_text(json.dumps({'name': name}))
        return self

    def set_template(self, relative, data):
        (self.manager / 'skills/_shared/templates/plugin' / relative).write_bytes(data)

    def drop_template(self, relative):
        (self.manager / 'skills/_shared/templates/plugin' / relative).unlink()
