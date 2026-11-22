"""Add missing shared development files to a selected plugin repository.

Existing regular files are never updated: deviations are only reported. Writes are
limited to missing files/directories, one ignore rule, the operator preference
(through operator_language.py) and the ownership lock.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
MANAGER_ROOT = HERE.parents[2]  # scripts -> _shared -> skills -> plugin root
TEMPLATE_BASE = 'templates/plugin'  # relative to skills/_shared
# Explicit, closed list: project path == template path (bytes are copied unchanged).
MANAGED_FILES = (
    'keep.md',
    'remove.md',
    'CLAUDE.md',
    'scripts/plugin.py',
    'scripts/verify.py',
    'scripts/run_tests.py',
    'install.sh',
    'skills/_shared/scripts/operator_language.py',
    'skills/_shared/references/operator-language.md',
)
# A folder without plugin.json is a valid target when it holds nothing but these top-level entries plus the
# skeleton paths below (names only; .git and .idea are never opened).
FRESH_ENTRIES = ('.git', '.idea', '.gitignore', '.project', 'scripts', 'skills', 'install.sh', 'CLAUDE.md', 'keep.md', 'remove.md')
PROJECT_ENTRIES = ('operator.json', 'plugin.skeleton.lock.json')
IGNORE_RULE = '/.project/operator.json'
LOCK_PATH = '.project/plugin.skeleton.lock.json'
LANGUAGE_PATH = '.project/operator.json'
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
SHA256 = re.compile(r'[0-9a-f]{64}')


class Conflict(Exception):
    def __init__(self, path, reason, code=None, entries=None):
        super().__init__(reason)
        self.path, self.reason, self.code, self.entries = path, reason, code, entries


def load_language_helper():
    spec = importlib.util.spec_from_file_location('operator_language_for_setup', HERE / 'operator_language.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_json(text):
    def pairs(items):
        keys = [key for key, _ in items]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate JSON key')
        return dict(items)
    return json.loads(text, object_pairs_hook=pairs)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def lstat(path):
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def check_chain(root, relative, final):
    """Reject symlinks, traversal and wrong types along root/relative.

    final: 'file' or 'dir'. Returns 'missing' or 'present'."""
    parts = relative.split('/')
    if (not relative or relative.startswith('/') or '\\' in relative
            or any(part in ('', '.', '..') for part in parts)):
        raise Conflict(relative, 'Unsafe path')
    current = root
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = lstat(current)
        except OSError as exc:
            raise Conflict(relative, 'Cannot inspect ' + '/'.join(parts[:index + 1]) + ': ' + (exc.strerror or str(exc))) from exc
        last = index == len(parts) - 1
        if info is None:
            return 'missing'
        if stat.S_ISLNK(info.st_mode):
            raise Conflict(relative, 'Symlink in managed path: ' + '/'.join(parts[:index + 1]))
        wanted_dir = not last or final == 'dir'
        if wanted_dir and not stat.S_ISDIR(info.st_mode):
            raise Conflict(relative, 'Path conflict: ' + '/'.join(parts[:index + 1]) + ' exists but is not a directory')
        if not wanted_dir and not stat.S_ISREG(info.st_mode):
            raise Conflict(relative, 'Path conflict: ' + relative + ' exists but is not a regular file')
    return 'present'


def read_regular(root, relative):
    try:
        return (root / relative).read_bytes()
    except OSError as exc:
        raise Conflict(relative, 'Cannot read: ' + exc.strerror) from exc


def skeleton_paths():
    files = set(MANAGED_FILES)
    directories = {d for f in MANAGED_FILES for d in (f.rsplit('/', i)[0] for i in range(1, f.count('/') + 1))}
    return files, directories


def classify_unconfigured(root):
    """Accept a folder without plugin.json only if it holds nothing but metadata and skeleton paths.

    .git and .idea are only checked for being real directories, never opened or read."""
    names = sorted(os.listdir(root))
    others = [n for n in names if n not in FRESH_ENTRIES]
    files, directories = skeleton_paths()
    for top in ('scripts', 'skills'):  # walk only the skeleton folders; unknown names are foreign content
        if top in names and os.path.isdir(root / top) and not os.path.islink(root / top):
            stack = [top]
            while stack:
                current = stack.pop()
                for child in sorted(os.listdir(root / current)):
                    relative = current + '/' + child
                    if relative in directories and os.path.isdir(root / relative) and not os.path.islink(root / relative):
                        stack.append(relative)
                    elif relative not in files and relative not in directories:
                        others.append(relative)
                    elif relative in directories:
                        pass  # symlink or file where a folder belongs: reported by inspect()
    if 'install.sh' in names and 'install.sh' not in files:
        others.append('install.sh')
    if others:
        raise Conflict('.', 'Folder has other content and is not an initializable plugin folder: ' + ', '.join(others),
                       'not_fresh', sorted(others))
    for entry in ('.git', '.idea'):
        if entry in names:
            check_chain(root, entry, 'dir')
    if '.gitignore' in names:
        read_ignore(root)  # regular, non-symlink, UTF-8; content is preserved and only extended later
    if '.project' in names:
        check_chain(root, '.project', 'dir')
        inner = sorted(os.listdir(root / '.project'))
        extra = [n for n in inner if n not in PROJECT_ENTRIES]
        if extra:
            raise Conflict('.project', 'Folder has other content and is not an initializable plugin folder: .project/'
                           + ', .project/'.join(extra), 'not_fresh', ['.project/' + n for n in extra])
        try:
            load_language_helper().preference(root)  # validates the stored preference without writing
        except (ValueError, OSError) as exc:
            raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    return names


def detect_target(target, allow_unconfigured=False):
    """Return (root, plugin name or None, state); state is 'plugin' or, without plugin.json, 'unconfigured'."""
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.is_symlink():
        raise Conflict('.', 'Target is a symlink; select the real directory')
    root = path.resolve()
    if not root.is_dir():
        raise Conflict('.', 'Target directory does not exist')
    if root == MANAGER_ROOT:
        raise Conflict('.', 'The embedded Plugin Manager is not a setup target')
    if check_chain(root, 'marketplace.json', 'file') == 'present':
        raise Conflict('marketplace.json', 'Marketplace repositories are not setup targets', 'marketplace')
    if check_chain(root, 'plugin.json', 'file') == 'missing':
        if allow_unconfigured:
            classify_unconfigured(root)
            return root, None, 'unconfigured'
        raise Conflict('plugin.json', 'Select a standalone plugin repository with a canonical plugin.json; '
                       'an unconfigured folder is handled by the central entry (status, language, skeleton, configure)', 'no_plugin')
    try:
        manifest = strict_json(read_regular(root, 'plugin.json').decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Conflict('plugin.json', 'Invalid plugin.json: ' + str(exc)) from exc
    name = manifest.get('name') if isinstance(manifest, dict) else None
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise Conflict('plugin.json', 'plugin.json needs a valid plugin name')
    if name == 'plugin-manager':
        raise Conflict('plugin.json', 'The embedded Plugin Manager is not a setup target')
    return root, name, 'plugin'


def load_templates():
    """Read the template sources. A single missing source of a managed path means "removed in the parent"
    (value None); a missing/invalid template base, symlinks, wrong types and read errors are conflicts."""
    base = HERE.parent / TEMPLATE_BASE
    try:
        if check_chain(HERE.parent, TEMPLATE_BASE, 'dir') == 'missing':
            raise Conflict('.', 'Template base is missing: ' + str(base), 'template_base')
    except Conflict as conflict:
        if conflict.code == 'template_base':
            raise
        raise Conflict('.', 'Template base invalid: ' + conflict.reason, 'template_base') from conflict
    result = {}
    for relative in MANAGED_FILES:
        source = TEMPLATE_BASE + '/' + relative
        try:
            if check_chain(HERE.parent, source, 'file') == 'missing':
                result[relative] = None  # source removed in the parent
                continue
            path = HERE.parent / source
            mode = os.lstat(path).st_mode
            data = path.read_bytes()
        except Conflict as conflict:
            raise Conflict(relative, 'Template source invalid: ' + conflict.reason) from conflict
        except OSError as exc:
            raise Conflict(relative, 'Template source unreadable: ' + (exc.strerror or str(exc))) from exc
        if not data:
            raise Conflict(relative, 'Template source is empty')
        result[relative] = (data, bool(mode & 0o111))
    if all(entry is None for entry in result.values()):
        raise Conflict('.', 'No template source found for any managed file; refusing to treat that as removal', 'template_base')
    return result


LOCK_VERSION = 2


def pair(source_hash, local_hash):
    return {'source_hash': source_hash, 'local_hash': local_hash}


def read_lock(root):
    """Current format only (schema_version 2); anything else is rejected and left untouched."""
    state = check_chain(root, LOCK_PATH, 'file')
    if state == 'missing':
        return {}, False, None
    raw = read_regular(root, LOCK_PATH)
    try:
        data = strict_json(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Conflict(LOCK_PATH, 'Invalid lock file: ' + str(exc)) from exc
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'files'}
            or type(data['schema_version']) is not int or data['schema_version'] != LOCK_VERSION
            or not isinstance(data['files'], dict)):
        raise Conflict(LOCK_PATH, 'Unsupported lock format (only schema_version ' + str(LOCK_VERSION)
                       + '); existing data preserved, no migration', 'lock_format')
    for key, value in data['files'].items():
        try:
            check_chain(root, key, 'file')
        except Conflict as exc:
            raise Conflict(LOCK_PATH, 'Unsafe lock path ' + repr(key)) from exc
        if (not isinstance(value, dict) or set(value) != {'source_hash', 'local_hash'}
                or not (isinstance(value['local_hash'], str) and SHA256.fullmatch(value['local_hash']))
                or not (value['source_hash'] is None
                        or (isinstance(value['source_hash'], str) and SHA256.fullmatch(value['source_hash'])))):
            raise Conflict(LOCK_PATH, 'Invalid lock entry for ' + key)
    return {k: dict(v) for k, v in data['files'].items()}, True, raw


def classify(local, template, accepted):
    """State of an existing file against the template and its accepted hash pair (rules of the sync)."""
    if local == template:
        return 'identical', None
    current = pair(sha256(template), sha256(local))
    if accepted == current:
        return 'accepted', None
    if accepted is None:
        return 'decision_needed', 'no_accepted_pair'
    source_changed, local_changed = accepted['source_hash'] != current['source_hash'], accepted['local_hash'] != current['local_hash']
    return 'decision_needed', ('both_changed' if source_changed and local_changed
                               else 'source_changed' if source_changed else 'local_changed')


def read_ignore(root):
    state = check_chain(root, '.gitignore', 'file')
    if state == 'missing':
        return None
    try:
        return read_regular(root, '.gitignore').decode('utf-8')
    except UnicodeDecodeError as exc:
        raise Conflict('.gitignore', '.gitignore is not valid UTF-8') from exc


def has_rule(text):
    return text is not None and IGNORE_RULE in [line.rstrip('\r') for line in text.split('\n')]


def inspect(root, requested_language):
    """Read-only plan; raises Conflict before any write could happen."""
    language = load_language_helper()
    if requested_language is not None:
        try:
            language.validate_language(requested_language)
        except ValueError as exc:
            raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    templates = load_templates()
    check_chain(root, '.project', 'dir')
    try:
        preference = language.preference(root)
    except (ValueError, OSError) as exc:  # includes corrupt JSON (JSONDecodeError)
        raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    if requested_language and preference['operator_language'] not in (None, requested_language):
        raise Conflict(LANGUAGE_PATH, 'Operator language is already ' + preference['operator_language']
                       + '; changing it is not part of setup')
    lock, lock_exists, _ = read_lock(root)
    ignore_text = read_ignore(root)
    files, directories, decisions = {}, [], []
    removals = {'auto': [], 'decisions': [], 'kept': [], 'unowned': [], 'lock_cleanup': []}
    needed_dirs = set()
    for relative, entry in templates.items():
        accepted = lock.get(relative)
        exists = check_chain(root, relative, 'file') != 'missing'
        if entry is None:  # source removed in the parent: ownership evidence in the lock decides
            local = read_regular(root, relative) if exists else None
            if not exists:
                files[relative] = 'removed'
                if accepted is not None:
                    removals['lock_cleanup'].append(relative)
            elif accepted is None:
                files[relative] = 'unowned'  # no ownership evidence: never touched
                removals['unowned'].append(relative)
            else:
                local_hash = sha256(local)
                if accepted['source_hash'] is None and local_hash == accepted['local_hash']:
                    files[relative] = 'removal_kept'
                    removals['kept'].append(relative)
                elif (accepted['source_hash'] is not None
                        and local_hash == accepted['local_hash'] == accepted['source_hash']):
                    files[relative] = 'auto_remove'
                    removals['auto'].append(relative)
                else:
                    files[relative] = 'removal_decision'
                    removals['decisions'].append({
                        'kind': 'removal', 'path': relative, 'source_removed': True,
                        'reason': 'source_removed_local_changed' if accepted['source_hash'] is None else 'source_removed_local_differs',
                        'source_hash': None, 'local_hash': local_hash, 'accepted': accepted,
                        'source_file': None, 'local_file': str(root / relative)})
            continue
        template = entry[0]
        parent = ''
        for part in relative.split('/')[:-1]:
            parent += part
            needed_dirs.add(parent)
            parent += '/'
        if not exists:
            files[relative] = 'missing'
        else:
            local = read_regular(root, relative)
            files[relative], reason = classify(local, template, accepted)
            if reason:
                current = pair(sha256(template), sha256(local))
                decisions.append({
                    'kind': 'content', 'path': relative, 'reason': reason, 'source_hash': current['source_hash'],
                    'local_hash': current['local_hash'], 'accepted': accepted,
                    'source_changed': accepted is None or accepted['source_hash'] != current['source_hash'],
                    'local_changed': accepted is None or accepted['local_hash'] != current['local_hash'],
                    'source_file': str(HERE.parent / TEMPLATE_BASE / relative), 'local_file': str(root / relative)})
        parent = ''
        for part in relative.split('/')[:-1]:
            parent += part
            if check_chain(root, parent, 'dir') == 'missing' and parent not in directories:
                directories.append(parent)
            parent += '/'
    pending = [r for r, state in files.items()
               if state in ('missing', 'identical') and lock.get(r) != pair(sha256(templates[r][0]), sha256(templates[r][0]))]
    return {'language': language, 'preference': preference, 'templates': templates, 'lock': lock,
            'lock_exists': lock_exists, 'ignore_text': ignore_text, 'files': files,
            'directories': directories, 'pending': pending, 'decisions': decisions, 'removals': removals,
            'needed_dirs': needed_dirs,
            'rule_pending': preference['operator_language'] is not None and not has_rule(ignore_text)}


def next_flow(operation, failed, needs_choice, plan, missing, state):
    """Fixed priority: conflict/error stops; then language, skeleton, sync decisions, configuration, ready.
    Flow operations (setup) only say to run status again; status decides."""
    if failed:
        return 'stop'
    if operation != 'status':
        return 'status'
    if needs_choice:
        return 'language'
    removals = plan['removals']
    if missing or plan['pending'] or plan['rule_pending'] or removals['auto'] or removals['lock_cleanup']:
        return 'skeleton'
    if plan['decisions'] or removals['decisions']:
        return 'sync'
    return 'configure' if state == 'unconfigured' else 'ready'


def report(operation, root, name, plan, created_files=(), created_dirs=(), lock_changed=False,
           ignore=None, saved=False, errors=(), conflicts=(), unverified=(), state='plugin', removed_files=(), removed_dirs=()):
    files = plan['files']
    preference = plan['preference']
    different = sorted(r for r, s in files.items() if s in ('accepted', 'decision_needed'))
    missing = sorted(r for r, s in files.items() if s == 'missing')
    directories = list(plan['directories'])
    if ('.project' not in directories and not os.path.isdir(root / '.project')
            and (plan['pending'] or preference['needs_choice'])):
        directories.append('.project')  # management folder needed for language and/or lock
    failed = bool(errors or conflicts)
    return {
        'operation': operation, 'ok': not failed, 'state': state, 'target': str(root), 'plugin': name,
        'plugin_configured': state == 'plugin',
        'next': next_flow(operation, failed, preference['needs_choice'], plan, missing, state),
        'skeleton': {'open': bool(missing or plan['pending'] or plan['rule_pending'] or plan['removals']['auto']
                                  or plan['removals']['lock_cleanup']) if operation == 'status' else failed,
                     'missing_files': missing, 'lock_pending': list(plan['pending']) if operation == 'status' else [],
                     'ignore_rule_pending': plan['rule_pending'] if operation == 'status' else False,
                     'different': different,
                     'accepted_deviations': sorted(r for r, s in files.items() if s == 'accepted')},
        'sync': {'needed': bool(plan['decisions'] or plan['removals']['decisions']) if operation == 'status' else False,
                 'decisions': list(plan['decisions']) if operation == 'status' else []},
        'removals': {'auto': list(plan['removals']['auto']), 'decisions': list(plan['removals']['decisions']),
                     'kept': list(plan['removals']['kept']), 'unowned': list(plan['removals']['unowned']),
                     'lock_cleanup': list(plan['removals']['lock_cleanup'])} if operation == 'status'
        else {'auto': [], 'decisions': [], 'kept': [], 'unowned': [], 'lock_cleanup': []},
        'removed': {'files': list(removed_files), 'directories': list(removed_dirs)},
        'conflicts': list(conflicts), 'errors': list(errors),
        'files': dict(files),
        'missing': {'files': missing, 'directories': [d for d in directories if not os.path.isdir(root / d)]},
        'identical': sorted(r for r, s in files.items() if s == 'identical'),
        'different': different,
        'created': {'files': list(created_files), 'directories': list(created_dirs), 'unverified': list(unverified)},
        'language': {'operator_language': preference['operator_language'], 'needs_choice': preference['needs_choice'],
                     'saved': saved},
        'gitignore': ignore or {'rule_present': has_rule(plan['ignore_text']), 'changed': False},
        'lock': {'path': LOCK_PATH, 'exists': plan['lock_exists'] or lock_changed, 'changed': lock_changed,
                 'pending': [] if operation == 'setup' and not failed else list(plan['pending'])},
        'matches_template': all(s in ('identical', 'removed') for s in files.values()) and not failed,
        'target_code_executed': False,
        'limitations': ['Existing regular files are replaced only by an explicit adopt decision (sync); deviations are otherwise only reported.',
                        'Ignore handling checks only the exact line ' + IGNORE_RULE + '; other rules and negations are not evaluated.'],
    }


def status(target):
    root, name, state = detect_target(target, allow_unconfigured=True)
    plan = inspect(root, None)
    return dict(report('status', root, name, plan, state=state), entries=sorted(os.listdir(root)))


def atomic_write(path, data, mode=None):
    descriptor, temporary = tempfile.mkstemp(prefix='.setup-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def current_umask():
    value = os.umask(0)
    os.umask(value)
    return value


def copy_new(path, data, executable):
    """Create path from data without ever replacing an existing entry.

    Returns True when created; False if the entry appeared meanwhile."""
    mode = (0o777 if executable else 0o666) & ~current_umask()
    descriptor, temporary = tempfile.mkstemp(prefix='.setup-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        try:
            os.link(temporary, path)  # atomic and fails if path exists
        except FileExistsError:
            return False
        return True
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def ensure_directory(path, created):
    if not path.exists():
        path.mkdir()
        created.append(path)


def add_ignore_rule(root):
    """Add the rule to the CURRENT .gitignore (re-read now, never the planning snapshot)."""
    path = root / '.gitignore'
    for _ in range(3):
        text = read_ignore(root)
        if has_rule(text):
            return {'rule_present': True, 'changed': False}
        if text is None:
            body, mode = (IGNORE_RULE + '\n').encode(), 0o666 & ~current_umask()
        else:
            newline = '\r\n' if '\r\n' in text else '\n'
            addition = ('' if text == '' or text.endswith('\n') else newline) + IGNORE_RULE + newline
            body, mode = (text + addition).encode('utf-8'), stat.S_IMODE(os.stat(path).st_mode)
        if replace_if_unchanged(path, body, mode, None if text is None else text.encode('utf-8')):
            return {'rule_present': True, 'changed': True, 'created': text is None}
    raise OSError('.gitignore kept changing during setup; nothing was overwritten')


def current_bytes(path):
    info = lstat(path)
    if info is None:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise OSError(str(path) + ' is no longer a regular file')
    return path.read_bytes()


def replace_if_unchanged(path, data, mode, expected):
    """Replace path only if it still holds `expected` (None = absent); False if it changed.

    Narrow best-effort check; not protection against arbitrary concurrent writers."""
    descriptor, temporary = tempfile.mkstemp(prefix='.setup-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        if current_bytes(path) != expected:
            return False
        os.replace(temporary, path)
        return True
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_lock(root, evidence, remove=()):
    """Merge verified pairs into the CURRENT lock and drop `remove` entries; retry when it changed meanwhile."""
    path = root / LOCK_PATH
    for _ in range(3):
        try:
            lock, exists, expected = read_lock(root)  # parsed value and raw bytes from ONE read
        except Conflict as conflict:
            raise OSError('Lock became invalid during setup: ' + conflict.reason) from conflict
        merged = {k: v for k, v in lock.items() if k not in remove}
        merged.update(evidence)
        if merged == lock:
            return False
        body = (json.dumps({'schema_version': LOCK_VERSION, 'files': dict(sorted(merged.items()))}, indent=2) + '\n').encode()
        if replace_if_unchanged(path, body, 0o666 & ~current_umask(), expected):
            return True
    raise OSError('Lock file kept changing during setup; nothing was overwritten')


def language_only(target, requested_language):
    """Save the operator language (no plugin.json, Git or origin needed): ignore rule first, then helper."""
    root, name, state = detect_target(target, allow_unconfigured=True)
    plan = inspect(root, requested_language)  # every technical conflict is detected before the first write
    language, preference, ignore_text = plan['language'], plan['preference'], plan['ignore_text']
    created_dirs, errors, conflicts, saved = [], [], [], False
    ignore = {'rule_present': has_rule(ignore_text), 'changed': False}
    project_existed = os.path.lexists(root / '.project')
    try:
        if not has_rule(ignore_text):
            ignore = add_ignore_rule(root)
        if preference['operator_language'] is None:
            language.preference(root, requested_language)
            saved = True
    except Conflict as conflict:
        conflicts.append({'path': conflict.path, 'reason': conflict.reason})
    except (OSError, ValueError) as exc:
        errors.append('Write failed: ' + str(exc))
    if not project_existed and os.path.isdir(root / '.project'):
        created_dirs.append('.project')
    failed = bool(errors or conflicts)
    stored = preference['operator_language'] or (requested_language if saved else None)
    return {'operation': 'language', 'ok': not failed, 'state': state, 'target': str(root), 'plugin': name,
            'conflicts': conflicts, 'errors': errors,
            'language': {'operator_language': stored, 'needs_choice': stored is None, 'saved': saved},
            'gitignore': ignore, 'created': {'files': [], 'directories': created_dirs},
            'next': 'stop' if failed else 'status', 'target_code_executed': False}


def setup(target, requested_language=None):
    root, name, state = detect_target(target, allow_unconfigured=True)
    plan = inspect(root, requested_language)  # fresh check immediately before any write; conflicts end here
    templates, files = plan['templates'], dict(plan['files'])
    preference = plan['preference']
    chosen = preference['operator_language'] or requested_language
    created_files, created_dirs, unverified, errors, conflicts = [], [], [], [], []
    removed_files, removed_dirs = [], []
    ignore = {'rule_present': has_rule(plan['ignore_text']), 'changed': False}
    saved = lock_changed = False
    project_existed = os.path.lexists(root / '.project')
    try:
        for relative in plan['directories']:
            ensure_directory(root / relative, created_dirs)
        if chosen and not has_rule(plan['ignore_text']):
            ignore = add_ignore_rule(root)
        if requested_language and preference['operator_language'] is None:
            plan['language'].preference(root, requested_language)
            preference = {'operator_language': requested_language, 'needs_choice': False}
            saved = True
        for relative in MANAGED_FILES:
            if files[relative] != 'missing':
                continue
            data, executable = templates[relative]
            destination = root / relative
            if copy_new(destination, data, executable):
                created_files.append(relative)  # created now, verified below
                files[relative] = 'unverified'
                unverified.append(relative)
                if destination.read_bytes() != data:
                    raise OSError('Copied content does not match template: ' + relative)
                files[relative] = 'identical'
                unverified.remove(relative)
            else:  # appeared between check and copy: never overwrite; re-check type, then classify
                files[relative] = 'conflict'
                check_chain(root, relative, 'file')
                files[relative] = classify(read_regular(root, relative), data, plan['lock'].get(relative))[0]
        for relative, file_state in files.items():  # content may have changed since classification
            if file_state != 'identical':
                continue
            files[relative] = 'conflict'  # stays so unless the file is read successfully as a regular file
            check_chain(root, relative, 'file')
            current = read_regular(root, relative)
            files[relative] = classify(current, templates[relative][0], plan['lock'].get(relative))[0]
        for relative in plan['removals']['auto']:  # source removed, local file untouched since it was identical
            files[relative] = 'conflict'  # stays so if the verification below fails
            remove_managed_file(root, relative, plan['lock'][relative]['local_hash'], plan['needed_dirs'],
                                removed_files, removed_dirs)
            files[relative] = 'removed'
        drop = [*plan['removals']['lock_cleanup'], *removed_files]
        evidence = {r: pair(sha256(templates[r][0]), sha256(templates[r][0])) for r, file_state in files.items() if file_state == 'identical'}
        if evidence or drop:
            if evidence:
                ensure_directory(root / '.project', created_dirs)
            lock_changed = write_lock(root, evidence, remove=drop)
    except Conflict as conflict:
        conflicts.append({'path': conflict.path, 'reason': conflict.reason})
    except (OSError, ValueError) as exc:
        errors.append('Write failed: ' + str(exc) + ' (partial changes are listed under created/language/gitignore)')
    if not project_existed and os.path.isdir(root / '.project') and root / '.project' not in created_dirs:
        created_dirs.append(root / '.project')  # also when only the language helper created it
    plan = dict(plan, files=files, preference=preference)
    return report('setup', root, name, plan, created_files, [str(Path(d).relative_to(root)) for d in created_dirs],
                  lock_changed, ignore, saved, errors, conflicts, unverified, state, removed_files, removed_dirs)


def remove_managed_file(root, relative, expected_hash, needed_dirs, done_files, done_dirs):
    """Delete one verified managed file, then empty parent folders bottom-up with rmdir.

    Only parents of the removed file are considered; folders that are not empty, still needed by the
    current skeleton, links or non-folders stop the cleanup. Nothing is ever deleted recursively."""
    check_chain(root, relative, 'file')
    if sha256(read_regular(root, relative)) != expected_hash:
        raise Conflict(relative, 'File changed since it was checked; check status again', 'stale_decision')
    os.unlink(root / relative)
    done_files.append(relative)
    parts = relative.split('/')[:-1]
    for count in range(len(parts), 0, -1):
        folder = '/'.join(parts[:count])
        info = lstat(root / folder)
        if (folder in needed_dirs or info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
                or os.listdir(root / folder)):
            break
        os.rmdir(root / folder)
        done_dirs.append(folder)


def sync(target, decision, relative, expected_source, expected_local):
    """Apply ONE explicit decision for a managed file, for exactly the shown hashes.

    Content decisions (source and local differ): keep records the current pair, adopt replaces the file by the
    template (mode kept). Removal decisions (source removed in the parent): keep records {source_hash: null,
    local_hash}, delete removes the verified file, its lock entry and then only empty parent folders.
    For removal decisions the expected source is the literal `removed`."""
    root, name, state = detect_target(target, allow_unconfigured=True)
    plan = inspect(root, None)  # all technical conflicts (including an old lock format) end here, before writes
    if not SHA256.fullmatch(expected_local or '') or not (expected_source == 'removed' or SHA256.fullmatch(expected_source or '')):
        raise Conflict(relative, 'Expected hashes must be 64 lowercase hex characters (source: or "removed")', 'invalid_hash')
    if relative not in MANAGED_FILES:
        raise Conflict(relative, 'Not a managed file', 'unknown_path')
    item = next((d for d in plan['decisions'] + plan['removals']['decisions'] if d['path'] == relative), None)
    if item is None:
        raise Conflict(relative, 'No decision is open for this file; check status again', 'no_decision')
    if (item['source_hash'] or 'removed', item['local_hash']) != (expected_source, expected_local):
        raise Conflict(relative, 'The decision was made for a different source/local pair; check status again', 'stale_decision')
    if decision not in (('keep', 'adopt') if item['kind'] == 'content' else ('keep', 'delete')):
        raise Conflict(relative, 'This decision is not valid for a ' + item['kind'] + ' question', 'invalid_decision')
    destination = root / relative
    errors, conflicts, created_dirs, removed_files, removed_dirs = [], [], [], [], []
    file_changed = lock_changed = False
    evidence = None
    project_existed = os.path.lexists(root / '.project')
    try:
        if decision == 'adopt':
            template = plan['templates'][relative][0]
            local = destination.read_bytes()
            mode = stat.S_IMODE(os.lstat(destination).st_mode)  # modes of existing files are not changed
            if not replace_if_unchanged(destination, template, mode, local):
                raise OSError(relative + ' changed while adopting; nothing was replaced')
            file_changed = True
            if destination.read_bytes() != template:
                raise OSError('Replaced content does not match template: ' + relative)
            evidence = pair(item['source_hash'], item['source_hash'])
        elif decision == 'delete':
            remove_managed_file(root, relative, item['local_hash'], plan['needed_dirs'], removed_files, removed_dirs)
            lock_changed = write_lock(root, {}, remove=(relative,))
        else:
            evidence = pair(item['source_hash'], item['local_hash'])
        if evidence is not None:
            ensure_directory(root / '.project', created_dirs)
            lock_changed = write_lock(root, {relative: evidence})
    except Conflict as conflict:
        conflicts.append({'path': conflict.path, 'reason': conflict.reason})
    except (OSError, ValueError) as exc:
        errors.append('Write failed: ' + str(exc) + ' (partial changes: see changed and removed)')
    file_changed = file_changed or bool(removed_files)  # derived from what was actually deleted, also after errors
    if not project_existed and os.path.isdir(root / '.project') and root / '.project' not in created_dirs:
        created_dirs.append(root / '.project')  # same type as ensure_directory() appends: reported once
    failed = bool(errors or conflicts)
    return {'operation': 'sync', 'ok': not failed, 'state': state, 'target': str(root), 'plugin': name,
            'decision': decision, 'path': relative, 'conflicts': conflicts, 'errors': errors,
            'changed': {'file': file_changed, 'lock': lock_changed},
            'recorded': evidence if lock_changed else None,
            'removed': {'files': removed_files, 'directories': removed_dirs},
            'created': {'files': [], 'directories': [str(d.relative_to(root)) for d in created_dirs]},
            'next': 'stop' if failed else 'status', 'target_code_executed': False}


def conflict_result(operation, target, conflict):
    entry = {'path': conflict.path, 'reason': conflict.reason}
    if conflict.code:
        entry['code'] = conflict.code
    if conflict.entries:
        entry['entries'] = conflict.entries
    return {'operation': operation, 'ok': False, 'state': 'conflict', 'next': 'stop', 'target': str(target), 'conflicts': [entry],
            'created': {'files': [], 'directories': []}, 'target_code_executed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    read = commands.add_parser('status', help='Write-free inspection of language and development files')
    add = commands.add_parser('setup', help='Add missing files, ignore rule, language and ownership lock')
    only = commands.add_parser('language', help='Fresh folder without plugin.json: save the operator language')
    only.add_argument('--language', required=True, help='Explicitly selected operator language tag')
    decide = commands.add_parser('sync', help='Apply one explicit keep/adopt decision for a deviating managed file')
    decide.add_argument('--decision', required=True, choices=('keep', 'adopt', 'delete'), help='keep: keep local file; adopt: take template (content question); delete: remove the file (removal question)')
    decide.add_argument('--path', required=True, help='Managed file path from status sync.decisions')
    decide.add_argument('--source-hash', required=True, help='source_hash shown by status for this decision, or the literal removed for a removal question')
    decide.add_argument('--local-hash', required=True, help='local_hash shown by status for this decision')
    for sub in (read, add, only, decide):
        sub.add_argument('--target', required=True, help='Explicitly selected plugin repository root')
    add.add_argument('--language', help='Explicitly selected operator language tag (de, en, pt-BR)')
    args = parser.parse_args(argv)
    try:
        result = {'status': lambda: status(args.target), 'setup': lambda: setup(args.target, args.language),
                  'language': lambda: language_only(args.target, args.language),
                  'sync': lambda: sync(args.target, args.decision, args.path, args.source_hash, args.local_hash)}[args.operation]()
    except Conflict as conflict:
        result = conflict_result(args.operation, args.target, conflict)
    except OSError as exc:  # expected filesystem failures outside the write phase
        result = conflict_result(args.operation, args.target, Conflict('.', 'Filesystem error: ' + (exc.strerror or str(exc))))
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
