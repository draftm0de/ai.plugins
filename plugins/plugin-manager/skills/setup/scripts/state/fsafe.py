"""Low-level, symlink-safe file access and atomic writes."""
import hashlib
import json
import os
import stat
import tempfile
from .constants import Conflict


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
