"""Helpers for operator-language tests; fictional temporary projects only."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
GENERATOR = ROOT / 'skills/_shared/templates/plugin/skills/_shared'
MANAGER = ROOT / 'skills/_shared'
HELPER = 'scripts/operator_language.py'
REFERENCE = 'references/operator-language.md'


def load(path):
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location('operator_language_under_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


def tree(path):
    """Relative path -> bytes (None for directories), for before/after comparison."""
    path = Path(path)
    return {str(p.relative_to(path)): (None if p.is_dir() else p.read_bytes()) for p in sorted(path.rglob('*'))}


def isolated_helper(directory):
    """Copy only the helper into a plugin-like tree that has no Manager checkout."""
    target = Path(directory) / 'installed plugin copy/skills/_shared/scripts'
    target.mkdir(parents=True)
    shutil.copy2(GENERATOR / HELPER, target / 'operator_language.py')
    return target / 'operator_language.py'


def run(helper, root, *args, cwd=None):
    environment = {'PATH': ''}  # no PYTHONPATH, no external programs
    return subprocess.run([sys.executable, '-B', '-I', str(helper), '--root', str(root), *args],
                          capture_output=True, text=True, cwd=cwd, env=environment)


class Sandbox:
    def make(self):
        self.temp = tempfile.TemporaryDirectory(prefix='operator language ')
        self.base = Path(self.temp.name).resolve()
        self.helper = isolated_helper(self.base)
        self.project = self.base / 'project with spaces'
        self.project.mkdir()
        return self

    def close(self):
        for path in self.base.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
        self.temp.cleanup()
