"""Operator language and the ignore rule for its preference file."""
import importlib.util
import os
import stat
from . import detection
from . import fsafe
from . import inspection
from .constants import Conflict, IGNORE_RULE


def load_language_helper(ctx):
    spec = importlib.util.spec_from_file_location('operator_language_for_setup', ctx.scripts_root / 'operator_language.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_ignore(root):
    state = fsafe.check_chain(root, '.gitignore', 'file')
    if state == 'missing':
        return None
    try:
        return fsafe.read_regular(root, '.gitignore').decode('utf-8')
    except UnicodeDecodeError as exc:
        raise Conflict('.gitignore', '.gitignore is not valid UTF-8') from exc


def has_rule(text):
    return text is not None and IGNORE_RULE in [line.rstrip('\r') for line in text.split('\n')]


def add_ignore_rule(root):
    """Add the rule to the CURRENT .gitignore (re-read now, never the planning snapshot)."""
    path = root / '.gitignore'
    for _ in range(3):
        text = read_ignore(root)
        if has_rule(text):
            return {'rule_present': True, 'changed': False}
        if text is None:
            body, mode = (IGNORE_RULE + '\n').encode(), 0o666 & ~fsafe.current_umask()
        else:
            newline = '\r\n' if '\r\n' in text else '\n'
            addition = ('' if text == '' or text.endswith('\n') else newline) + IGNORE_RULE + newline
            body, mode = (text + addition).encode('utf-8'), stat.S_IMODE(os.stat(path).st_mode)
        if fsafe.replace_if_unchanged(path, body, mode, None if text is None else text.encode('utf-8')):
            return {'rule_present': True, 'changed': True, 'created': text is None}
    raise OSError('.gitignore kept changing during setup; nothing was overwritten')


def language_only(ctx, target, requested_language):
    """Save the operator language (no plugin.json, Git or origin needed): ignore rule first, then helper."""
    root, name, state = detection.detect_target(ctx, target, allow_unconfigured=True)
    plan = inspection.inspect(ctx, root, requested_language)  # every technical conflict is detected before the first write
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
