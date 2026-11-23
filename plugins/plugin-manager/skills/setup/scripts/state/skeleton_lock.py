"""Skeleton ownership evidence (skeleton.json): hash pairs and file classification."""
import json
from . import fsafe
from .constants import Conflict, LOCK_VERSION, SHA256


def pair(source_hash, local_hash):
    return {'source_hash': source_hash, 'local_hash': local_hash}


def read_lock(ctx, root):
    """Current format only (schema_version 2); anything else is rejected and left untouched."""
    state = fsafe.check_chain(root, ctx.lock_path, 'file')
    if state == 'missing':
        return {}, False, None
    raw = fsafe.read_regular(root, ctx.lock_path)
    try:
        data = fsafe.strict_json(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Conflict(ctx.lock_path, 'Invalid lock file: ' + str(exc)) from exc
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'files'}
            or type(data['schema_version']) is not int or data['schema_version'] != LOCK_VERSION
            or not isinstance(data['files'], dict)):
        raise Conflict(ctx.lock_path, 'Unsupported lock format (only schema_version ' + str(LOCK_VERSION)
                       + '); existing data preserved, no migration', 'lock_format')
    for key, value in data['files'].items():
        try:
            fsafe.check_chain(root, key, 'file')
        except Conflict as exc:
            raise Conflict(ctx.lock_path, 'Unsafe lock path ' + repr(key)) from exc
        if (not isinstance(value, dict) or set(value) != {'source_hash', 'local_hash'}
                or not (isinstance(value['local_hash'], str) and SHA256.fullmatch(value['local_hash']))
                or not (value['source_hash'] is None
                        or (isinstance(value['source_hash'], str) and SHA256.fullmatch(value['source_hash'])))):
            raise Conflict(ctx.lock_path, 'Invalid lock entry for ' + key)
    return {k: dict(v) for k, v in data['files'].items()}, True, raw


def classify(local, template, accepted):
    """State of an existing file against the template and its accepted hash pair (rules of the sync)."""
    if local == template:
        return 'identical', None
    current = pair(fsafe.sha256(template), fsafe.sha256(local))
    if accepted == current:
        return 'accepted', None
    if accepted is None:
        return 'decision_needed', 'no_accepted_pair'
    source_changed, local_changed = accepted['source_hash'] != current['source_hash'], accepted['local_hash'] != current['local_hash']
    return 'decision_needed', ('both_changed' if source_changed and local_changed
                               else 'source_changed' if source_changed else 'local_changed')


def write_lock(ctx, root, evidence, remove=()):
    """Merge verified pairs into the CURRENT lock and drop `remove` entries; retry when it changed meanwhile."""
    path = root / ctx.lock_path
    for _ in range(3):
        try:
            lock, exists, expected = read_lock(ctx, root)  # parsed value and raw bytes from ONE read
        except Conflict as conflict:
            raise OSError('Lock became invalid during setup: ' + conflict.reason) from conflict
        merged = {k: v for k, v in lock.items() if k not in remove}
        merged.update(evidence)
        if merged == lock:
            return False
        body = (json.dumps({'schema_version': LOCK_VERSION, 'files': dict(sorted(merged.items()))}, indent=2) + '\n').encode()
        if fsafe.replace_if_unchanged(path, body, 0o666 & ~fsafe.current_umask(), expected):
            return True
    raise OSError('Lock file kept changing during setup; nothing was overwritten')
