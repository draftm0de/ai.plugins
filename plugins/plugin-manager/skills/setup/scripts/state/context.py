"""The explicit context of one helper call: where the sources are, which plugin runs, its kinds and the active skeleton.

Nothing here is module-global: every function that needs the context receives it as its first parameter `ctx`. Production
creates it with the defaults (the locations of this package); tests may pass their own source root."""
import os
from pathlib import Path
from . import fsafe
from .constants import Conflict, HASH_HINT, MANIFEST_KEYS, NAME, SHA256, SKELETON_PATH, SYNC_KEYS

STATE_DIR = Path(__file__).resolve().parent  # skills/setup/scripts/state
DEFAULT_SOURCE_ROOT = STATE_DIR.parents[2] / '_shared'  # skills/_shared: manifests, templates and the operator-language helper
DEFAULT_MANAGER_ROOT = STATE_DIR.parents[3]  # plugin root


class Context:
    """source_root: the data of the parent (manifests, templates); the shared scripts always come from this package's own plugin; manager_root: the Manager itself (never a target);
    plugin: the running plugin that owns the evidence; kinds: read from source_root; the active skeleton follows the
    kind that detect_target finds (use_kind)."""

    def __init__(self, plugin, source_root=None, manager_root=None):
        if not isinstance(plugin, str) or not NAME.fullmatch(plugin):
            raise Conflict('.', 'The running plugin needs a valid name (--plugin)', 'plugin_name')
        self.plugin = plugin
        self.lock_path = SKELETON_PATH.format(plugin=plugin)
        self.source_root = Path(source_root).resolve() if source_root is not None else DEFAULT_SOURCE_ROOT
        self.scripts_root = DEFAULT_SOURCE_ROOT / 'scripts'  # shared scripts (operator_language.py) are code, never mock data
        self.manager_root = Path(manager_root).resolve() if manager_root is not None else DEFAULT_MANAGER_ROOT
        self.kinds = read_kinds(self.source_root)
        self.use_kind(None)

    def use_kind(self, kind):
        """Select the skeleton of a configured kind; None (unconfigured) has no skeleton at all."""
        if kind is None:
            self.template_base, self.managed_files, self.sync_file = None, (), {}
        else:
            self.template_base, self.managed_files, self.sync_file = (self.kinds[kind]['base'], self.kinds[kind]['common'],
                                                                      self.kinds[kind]['files'])


def safe_relative(value):
    return (isinstance(value, str) and value != '' and not value.startswith('/') and '\\' not in value
            and all(part not in ('', '.', '..') for part in value.split('/')))


def read_kinds(source_root):
    """Read the kinds from skills/_shared/manifests/<kind>.json (product, derived) and the generated
    <kind>.sync.json (files with hash and executable bit, removed tombstones); the sources of the synced
    files live in skills/_shared/templates/<kind>/sync/."""
    kinds = {}
    base = source_root / 'manifests'
    if fsafe.check_chain(source_root, 'manifests', 'dir') == 'missing':
        raise Conflict('.', 'Template base is missing: ' + str(base), 'template_base')
    for filename in sorted(os.listdir(base)):
        name = filename[:-5]
        if not filename.endswith('.json') or not NAME.fullmatch(name):  # <kind>.sync.json has a dot: never a kind
            continue
        relative = 'manifests/' + filename
        data = read_template_json(source_root, relative)
        derived_ok = (isinstance(data, dict) and isinstance(data.get('derived'), list)
                      and all(isinstance(d, dict) and set(d) == {'path', 'generate', 'check'} and safe_relative(d['path'])
                              and isinstance(d['generate'], str) and isinstance(d['check'], str) for d in data['derived']))
        if not (isinstance(data, dict) and set(data) == MANIFEST_KEYS and type(data['schema_version']) is int
                and data['schema_version'] == 1 and derived_ok and type(data['requires_marketplace']) is bool
                and (data['product'] is None or safe_relative(data['product']))):
            raise Conflict(relative, 'Unsupported kind manifest (schema_version 1 with product, requires_marketplace, derived); no migration', 'template_base')
        sync_relative = 'manifests/' + name + '.sync.json'
        sync = read_template_json(source_root, sync_relative)
        files_ok = (isinstance(sync, dict) and set(sync) == SYNC_KEYS and type(sync['schema_version']) is int
                    and sync['schema_version'] == 1 and isinstance(sync['files'], dict) and isinstance(sync['removed'], list)
                    and all(safe_relative(k) and isinstance(v, dict) and set(v) == {'sha256', 'executable'}
                            and isinstance(v['sha256'], str) and SHA256.fullmatch(v['sha256']) and type(v['executable']) is bool
                            for k, v in sync['files'].items())
                    and all(safe_relative(v) for v in sync['removed']) and len(set(sync['removed'])) == len(sync['removed']))
        if not files_ok:
            raise Conflict(sync_relative, 'Unsupported or invalid sync file (schema_version 1 with files and removed)' + HASH_HINT, 'template_base')
        if set(sync['files']) & set(sync['removed']):
            raise Conflict(sync_relative, 'A path is listed as synced file and as removed: '
                           + ', '.join(sorted(set(sync['files']) & set(sync['removed']))) + HASH_HINT, 'template_base')
        kinds[name] = {'base': 'templates/' + name + '/sync', 'product': data['product'], 'requires_marketplace': data['requires_marketplace'],
                       'files': {k: dict(v) for k, v in sync['files'].items()}, 'removed': tuple(sync['removed']),
                       'common': tuple(sorted(sync['files'])) + tuple(sync['removed']), 'derived': tuple(data['derived'])}
    if not kinds:
        raise Conflict('.', 'No kind manifest found under manifests/', 'template_base')
    return kinds


def read_template_json(source_root, relative):
    try:
        fsafe.check_chain(source_root, relative, 'file')
        return fsafe.strict_json((source_root / relative).read_text(encoding='utf-8'))
    except (Conflict, ValueError, UnicodeDecodeError, OSError) as exc:
        raise Conflict(relative, 'Invalid kind file: ' + str(getattr(exc, 'reason', exc)) + HASH_HINT, 'template_base') from exc
