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
TEMPLATE_DIR = SHARED / 'templates/plugin/sync'
SETUP_SCRIPTS = ROOT / 'skills/setup/scripts'  # the setup state helper: setup_state.py and the package state/
HELPER = SETUP_SCRIPTS / 'setup_state.py'
DRIVER = ROOT / 'tests/support/run_state.py'  # the real command line with a context given in code
# Files of the real skeleton whose delivery the delivery/integration tests check. keep.md and remove.md (manual
# sync-test sources) are deliberately not listed: they may disappear from the real parent. Rule tests of the sync
# do not use this list at all; they use FictionalSandbox with fixed fictional bytes (see tests/README.md).
FILES = ('CLAUDE.md', 'scripts/plugin.py', 'scripts/verify.py', 'scripts/run_tests.py',
         'AGENTS.md', 'docs/standards/coding.md', 'docs/standards/messages.md', 'docs/standards/testing.md', 'docs/standards/skills.md',
         'skills/_shared/scripts/operator_language.py', 'skills/_shared/references/operator-language.md')
PLUGIN = 'plugin-manager'  # running plugin whose evidence the helper manages
LOCK = '.project/plugins/' + PLUGIN + '/skeleton.json'
EVIDENCE = '.project/plugins/' + PLUGIN + '/config.json'


def template(relative):
    return (SHARED / 'templates/plugin/sync' / relative).read_bytes()


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
    def make(self, name='demo-plugin', configured=True):
        """Isolated copy of the real parent DATA (manifests, templates); the scripts are the real ones, given this as context."""
        self.temp = tempfile.TemporaryDirectory(prefix='project setup ')
        self.base = Path(self.temp.name).resolve()
        self.manager = self.base / 'manager copy'
        for data in ('manifests', 'templates'):
            shutil.copytree(SHARED / data, self.manager / 'skills/_shared' / data, ignore=shutil.ignore_patterns('__pycache__'))
        self.source_root = self.manager / 'skills/_shared'
        self.ctx_args = {'source_root': self.source_root, 'manager_root': self.manager}
        self.project = self.base / 'my plugin'
        self.project.mkdir()
        (self.project / 'plugin.json').write_text(json.dumps({'name': name}))
        if configured:
            self.configure(name)
        return self

    requires_marketplace = True  # the real kind plugin belongs to exactly one marketplace (R21)
    MARKETPLACE = {'name': 'fictional-market'}  # the identity of a marketplace is its name

    def configure(self, artifact='demo-plugin', kind='plugin', marketplace=...):
        """Configuration evidence (schema 2) of the running plugin (R15); unconfigure() removes it again."""
        path = self.project / EVIDENCE
        path.parent.mkdir(parents=True, exist_ok=True)
        if marketplace is ...:
            marketplace = dict(self.MARKETPLACE) if kind == 'plugin' and self.requires_marketplace else None
        path.write_text(json.dumps({'schema_version': 2, 'plugin': PLUGIN, 'kind': kind, 'artifact': artifact,
                                    'configured_at': '2026-11-22T10:00:00Z', 'marketplace': marketplace}))

    def unconfigure(self):
        (self.project / EVIDENCE).unlink(missing_ok=True)
        (self.project / 'plugin.json').unlink(missing_ok=True)

    def close(self):
        for path in self.base.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
            elif path.is_file():
                path.chmod(0o644)
        self.temp.cleanup()

    def template(self, relative):
        return (self.manager / 'skills/_shared/templates/plugin/sync' / relative).read_bytes()

    def run(self, operation, *args, target=None, real=False):
        """The real command line (isolated mode) with this sandbox as context; real=True uses the real parent data."""
        args = args if '--plugin' in args else (*args, '--plugin', PLUGIN)
        source, manager = ('-', '-') if real else (str(self.source_root), str(self.manager))
        command = [sys.executable, '-B', '-I', str(DRIVER), str(SETUP_SCRIPTS), source, manager, operation, '--target',
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
    requires_marketplace = False  # the fictional kind has no marketplace
    """Runs the REAL, unchanged setup state scripts against a minimal
    fictional parent whose kind manifest lists the fictional files as common."""

    def make(self, name='demo-plugin', files=None, configured=True):
        self.files = dict(FICTIONAL if files is None else files)
        self.temp = tempfile.TemporaryDirectory(prefix='project setup fiction ')
        self.base = Path(self.temp.name).resolve()
        self.manager = self.base / 'fictional parent'
        self.source_root = self.manager / 'skills/_shared'
        self.ctx_args = {'source_root': self.source_root, 'manager_root': self.manager}
        self.removed = []
        manifests = self.manager / 'skills/_shared/manifests'
        manifests.mkdir(parents=True, exist_ok=True)
        (manifests / 'plugin.json').write_text(json.dumps({'schema_version': 1, 'product': 'plugin.json', 'requires_marketplace': False, 'derived': []}))
        for path, (data, executable) in self.files.items():
            target = self.sync_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if executable else 0o644)
        self.write_sync_file()
        self.project = self.base / 'my plugin'
        self.project.mkdir()
        (self.project / 'plugin.json').write_text(json.dumps({'name': name}))
        if configured:
            self.configure(name)
        return self

    @property
    def sync_dir(self):
        return self.manager / 'skills/_shared/templates/plugin/sync'

    def write_sync_file(self):
        """The generated hash file, built with the rules of scripts/skeleton_hashes.py from the sync/ folder."""
        files = {}
        for path in sorted(p for p in self.sync_dir.rglob('*') if p.is_file()):
            files[str(path.relative_to(self.sync_dir))] = {'sha256': digest(path.read_bytes()), 'executable': bool(path.stat().st_mode & 0o111)}
        (self.manager / 'skills/_shared/manifests/plugin.sync.json').write_text(
            json.dumps({'schema_version': 1, 'files': files, 'removed': sorted(self.removed)}, indent=2) + '\n')

    def set_template(self, relative, data):
        """The parent changes or re-adds a source: a returning tombstone path becomes an ordinary file again."""
        (self.sync_dir / relative).parent.mkdir(parents=True, exist_ok=True)
        (self.sync_dir / relative).write_bytes(data)
        if relative in self.removed:
            self.removed.remove(relative)
        self.write_sync_file()

    def drop_template(self, relative):
        """The source is removed in the parent: the file goes and its path becomes a tombstone."""
        (self.sync_dir / relative).unlink()
        self.removed.append(relative)
        self.write_sync_file()


class Loaded:
    """A fresh in-process setup state package with its Context. The public operations take the context implicitly;
    everything else (submodules for patching, Conflict, Context) is the package itself."""
    def __init__(self, package, ctx):
        self.package, self.ctx = package, ctx

    def __getattr__(self, name):
        return getattr(self.package, name)

    def status(self, target):
        return self.package.status(self.ctx, target)

    def gate(self, target):
        return self.package.gate(self.ctx, target)

    def setup(self, target, requested_language=None):
        return self.package.setup(self.ctx, target, requested_language)

    def language_only(self, target, requested_language):
        return self.package.language_only(self.ctx, target, requested_language)

    def sync(self, target, decision, relative, expected_source, expected_local):
        return self.package.sync(self.ctx, target, decision, relative, expected_source, expected_local)

    def record(self, target, kind, artifact):
        return self.package.record(self.ctx, target, kind, artifact)


def load_state(source_root=None, manager_root=None, plugin=PLUGIN):
    """A fresh in-process copy of the real setup state package with a context for the running plugin (R15);
    source_root/manager_root give it mock data (default: the real parent)."""
    for name in [n for n in sys.modules if n == 'state' or n.startswith('state.')]:
        del sys.modules[name]
    sys.path.insert(0, str(SETUP_SCRIPTS))
    import state
    return Loaded(state, state.Context(plugin, source_root, manager_root))
