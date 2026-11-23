"""The setup flow: missing skeleton files, evidence and the automatic removals."""
import os
from pathlib import Path
import stat
from . import detection
from . import fsafe
from . import inspection
from . import preferences
from . import reporting
from . import skeleton_lock
from .constants import Conflict


def ensure_plugin_dir(ctx, root, created):
    for relative in ('.project', '.project/plugins', '.project/plugins/' + ctx.plugin):
        fsafe.ensure_directory(root / relative, created)


def setup(ctx, target, requested_language=None):
    root, name, state = detection.detect_target(ctx, target, allow_unconfigured=True)
    if state == 'unconfigured':
        raise Conflict('.', 'Configure first: the skeleton depends on the configured kind (plugin or marketplace)', 'not_configured')
    plan = inspection.inspect(ctx, root, requested_language)  # fresh check immediately before any write; conflicts end here
    templates, files = plan['templates'], dict(plan['files'])
    preference = plan['preference']
    chosen = preference['operator_language'] or requested_language
    created_files, created_dirs, unverified, errors, conflicts = [], [], [], [], []
    removed_files, removed_dirs, updated_files = [], [], []
    ignore = {'rule_present': preferences.has_rule(plan['ignore_text']), 'changed': False}
    saved = lock_changed = False
    project_existed = os.path.lexists(root / '.project')
    try:
        for relative in plan['directories']:
            fsafe.ensure_directory(root / relative, created_dirs)
        if chosen and not preferences.has_rule(plan['ignore_text']):
            ignore = preferences.add_ignore_rule(root)
        if requested_language and preference['operator_language'] is None:
            plan['language'].preference(root, requested_language)
            preference = {'operator_language': requested_language, 'needs_choice': False}
            saved = True
        for relative in ctx.managed_files:
            if files[relative] != 'missing':
                continue
            data, executable = templates[relative]
            destination = root / relative
            if fsafe.copy_new(destination, data, executable):
                created_files.append(relative)  # created now, verified below
                files[relative] = 'unverified'
                unverified.append(relative)
                if destination.read_bytes() != data:
                    raise OSError('Copied content does not match template: ' + relative)
                files[relative] = 'identical'
                unverified.remove(relative)
            else:  # appeared between check and copy: never overwrite; re-check type, then classify
                files[relative] = 'conflict'
                fsafe.check_chain(root, relative, 'file')
                files[relative] = skeleton_lock.classify(fsafe.read_regular(root, relative), data, plan['lock'].get(relative))[0]
        for relative in plan['updates']:  # an unchanged exact copy of the old source: take the new source
            files[relative] = 'conflict'  # stays so if the verification below fails
            fsafe.check_chain(root, relative, 'file')
            local = fsafe.read_regular(root, relative)
            if fsafe.sha256(local) != plan['lock'][relative]['local_hash']:
                raise Conflict(relative, 'File changed since it was checked; check status again', 'stale_decision')
            data = templates[relative][0]
            mode = stat.S_IMODE(os.lstat(root / relative).st_mode)  # modes of existing files are not changed
            if not fsafe.replace_if_unchanged(root / relative, data, mode, local):
                raise OSError(relative + ' changed while updating; nothing was replaced')
            if (root / relative).read_bytes() != data:
                raise OSError('Replaced content does not match template: ' + relative)
            files[relative] = 'identical'
            updated_files.append(relative)
        for relative, file_state in files.items():  # content may have changed since classification
            if file_state != 'identical':
                continue
            files[relative] = 'conflict'  # stays so unless the file is read successfully as a regular file
            fsafe.check_chain(root, relative, 'file')
            current = fsafe.read_regular(root, relative)
            files[relative] = skeleton_lock.classify(current, templates[relative][0], plan['lock'].get(relative))[0]
        for relative in plan['removals']['auto']:  # source removed, local file untouched since it was identical
            files[relative] = 'conflict'  # stays so if the verification below fails
            remove_managed_file(root, relative, plan['lock'][relative]['local_hash'], plan['needed_dirs'],
                                removed_files, removed_dirs)
            files[relative] = 'removed'
        drop = [*plan['removals']['lock_cleanup'], *removed_files]
        evidence = {r: skeleton_lock.pair(fsafe.sha256(templates[r][0]), fsafe.sha256(templates[r][0])) for r, file_state in files.items() if file_state == 'identical'}
        if evidence or drop:
            if evidence:
                ensure_plugin_dir(ctx, root, created_dirs)
            lock_changed = skeleton_lock.write_lock(ctx, root, evidence, remove=drop)
    except Conflict as conflict:
        conflicts.append({'path': conflict.path, 'reason': conflict.reason})
    except (OSError, ValueError) as exc:
        errors.append('Write failed: ' + str(exc) + ' (partial changes are listed under created/language/gitignore)')
    if not project_existed and os.path.isdir(root / '.project') and root / '.project' not in created_dirs:
        created_dirs.append(root / '.project')  # also when only the language helper created it
    plan = dict(plan, files=files, preference=preference)
    return reporting.report(ctx, 'setup', root, name, plan, created_files, [str(Path(d).relative_to(root)) for d in created_dirs],
                  lock_changed, ignore, saved, errors, conflicts, unverified, state, removed_files, removed_dirs, updated_files)


def remove_managed_file(root, relative, expected_hash, needed_dirs, done_files, done_dirs):
    """Delete one verified managed file, then empty parent folders bottom-up with rmdir.

    Only parents of the removed file are considered; folders that are not empty, still needed by the
    current skeleton, links or non-folders stop the cleanup. Nothing is ever deleted recursively."""
    fsafe.check_chain(root, relative, 'file')
    if fsafe.sha256(fsafe.read_regular(root, relative)) != expected_hash:
        raise Conflict(relative, 'File changed since it was checked; check status again', 'stale_decision')
    os.unlink(root / relative)
    done_files.append(relative)
    parts = relative.split('/')[:-1]
    for count in range(len(parts), 0, -1):
        folder = '/'.join(parts[:count])
        info = fsafe.lstat(root / folder)
        if (folder in needed_dirs or info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
                or os.listdir(root / folder)):
            break
        os.rmdir(root / folder)
        done_dirs.append(folder)
