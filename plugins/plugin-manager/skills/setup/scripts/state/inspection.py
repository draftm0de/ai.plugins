"""The write-free inspection plan of a target folder."""
from . import fsafe
from . import preferences
from . import skeleton_lock
from . import template_sources
from .constants import Conflict, LANGUAGE_PATH


def inspect(ctx, root, requested_language):
    """Read-only plan; raises Conflict before any write could happen."""
    language = preferences.load_language_helper(ctx)
    if requested_language is not None:
        try:
            language.validate_language(requested_language)
        except ValueError as exc:
            raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    templates = template_sources.load_templates(ctx)
    fsafe.check_chain(root, '.project', 'dir')
    try:
        preference = language.preference(root)
    except (ValueError, OSError) as exc:  # includes corrupt JSON (JSONDecodeError)
        raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    if requested_language and preference['operator_language'] not in (None, requested_language):
        raise Conflict(LANGUAGE_PATH, 'Operator language is already ' + preference['operator_language']
                       + '; changing it is not part of setup')
    lock, lock_exists, _ = skeleton_lock.read_lock(ctx, root)
    ignore_text = preferences.read_ignore(root)
    files, directories, decisions = {}, [], []
    removals = {'auto': [], 'decisions': [], 'kept': [], 'unowned': [], 'lock_cleanup': []}
    needed_dirs = set()
    for relative, entry in templates.items():
        accepted = lock.get(relative)
        exists = fsafe.check_chain(root, relative, 'file') != 'missing'
        if entry is None:  # source removed in the parent: ownership evidence in the lock decides
            local = fsafe.read_regular(root, relative) if exists else None
            if not exists:
                files[relative] = 'removed'
                if accepted is not None:
                    removals['lock_cleanup'].append(relative)
            elif accepted is None:
                files[relative] = 'unowned'  # no ownership evidence: never touched
                removals['unowned'].append(relative)
            else:
                local_hash = fsafe.sha256(local)
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
            local = fsafe.read_regular(root, relative)
            files[relative], reason = skeleton_lock.classify(local, template, accepted)
            if reason:
                current = skeleton_lock.pair(fsafe.sha256(template), fsafe.sha256(local))
                decisions.append({
                    'kind': 'content', 'path': relative, 'reason': reason, 'source_hash': current['source_hash'],
                    'local_hash': current['local_hash'], 'accepted': accepted,
                    'source_changed': accepted is None or accepted['source_hash'] != current['source_hash'],
                    'local_changed': accepted is None or accepted['local_hash'] != current['local_hash'],
                    'source_file': str(ctx.source_root / ctx.template_base / relative), 'local_file': str(root / relative)})
        parent = ''
        for part in relative.split('/')[:-1]:
            parent += part
            if fsafe.check_chain(root, parent, 'dir') == 'missing' and parent not in directories:
                directories.append(parent)
            parent += '/'
    pending = [r for r, state in files.items()
               if state in ('missing', 'identical') and lock.get(r) != skeleton_lock.pair(fsafe.sha256(templates[r][0]), fsafe.sha256(templates[r][0]))]
    return {'language': language, 'preference': preference, 'templates': templates, 'lock': lock,
            'lock_exists': lock_exists, 'ignore_text': ignore_text, 'files': files,
            'directories': directories, 'pending': pending, 'decisions': decisions, 'removals': removals,
            'needed_dirs': needed_dirs,
            'rule_pending': preference['operator_language'] is not None and not preferences.has_rule(ignore_text)}
