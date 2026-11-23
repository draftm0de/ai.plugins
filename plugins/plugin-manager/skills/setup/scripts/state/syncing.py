"""The explicit keep/adopt/delete decision for one managed file."""
import os
import stat
from . import detection
from . import fsafe
from . import inspection
from . import skeleton
from . import skeleton_lock
from .constants import Conflict, SHA256


def sync(ctx, target, decision, relative, expected_source, expected_local):
    """Apply ONE explicit decision for a managed file, for exactly the shown hashes.

    Content decisions (source and local differ): keep records the current pair, adopt replaces the file by the
    template (mode kept). Removal decisions (source removed in the parent): keep records {source_hash: null,
    local_hash}, delete removes the verified file, its lock entry and then only empty parent folders.
    For removal decisions the expected source is the literal `removed`."""
    root, name, state = detection.detect_target(ctx, target, allow_unconfigured=True)
    if state == 'unconfigured':
        raise Conflict('.', 'Configure first: the skeleton depends on the configured kind (plugin or marketplace)', 'not_configured')
    plan = inspection.inspect(ctx, root, None)  # all technical conflicts (including an old lock format) end here, before writes
    if not SHA256.fullmatch(expected_local or '') or not (expected_source == 'removed' or SHA256.fullmatch(expected_source or '')):
        raise Conflict(relative, 'Expected hashes must be 64 lowercase hex characters (source: or "removed")', 'invalid_hash')
    if relative not in ctx.managed_files:
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
            if not fsafe.replace_if_unchanged(destination, template, mode, local):
                raise OSError(relative + ' changed while adopting; nothing was replaced')
            file_changed = True
            if destination.read_bytes() != template:
                raise OSError('Replaced content does not match template: ' + relative)
            evidence = skeleton_lock.pair(item['source_hash'], item['source_hash'])
        elif decision == 'delete':
            skeleton.remove_managed_file(root, relative, item['local_hash'], plan['needed_dirs'], removed_files, removed_dirs)
            lock_changed = skeleton_lock.write_lock(ctx, root, {}, remove=(relative,))
        else:
            evidence = skeleton_lock.pair(item['source_hash'], item['local_hash'])
        if evidence is not None:
            skeleton.ensure_plugin_dir(ctx, root, created_dirs)
            lock_changed = skeleton_lock.write_lock(ctx, root, {relative: evidence})
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
