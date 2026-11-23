"""Template sources of the synced files, checked against the recorded hashes."""
import os
from pathlib import Path
from . import fsafe
from .constants import Conflict, HASH_HINT


def load_templates(ctx):
    """Read the template sources of the synced files and check them against the recorded hashes. Paths in the
    removed list of the sync file are tombstones (value None: source removed in the parent); a missing or
    deviating source of a listed file, an unlisted file, a missing/invalid template base, symlinks, wrong types
    and read errors are conflicts, never removals."""
    if not ctx.managed_files:
        return {}
    base = ctx.source_root / ctx.template_base
    if ctx.sync_file:  # a kind without synced files needs no sync/ folder
        try:
            if fsafe.check_chain(ctx.source_root, ctx.template_base, 'dir') == 'missing':
                raise Conflict('.', 'Template base is missing: ' + str(base) + HASH_HINT, 'template_base')
        except Conflict as conflict:
            if conflict.code == 'template_base':
                raise
            raise Conflict('.', 'Template base invalid: ' + conflict.reason, 'template_base') from conflict
    result = {}
    removed = [r for r in ctx.managed_files if r not in ctx.sync_file]
    for relative in ctx.managed_files:
        if relative in removed:
            result[relative] = None  # tombstone: source removed in the parent
            continue
        source = ctx.template_base + '/' + relative
        try:
            if fsafe.check_chain(ctx.source_root, source, 'file') == 'missing':
                raise Conflict(relative, 'Template source of a listed file is missing' + HASH_HINT, 'template_base')
            path = ctx.source_root / source
            data = path.read_bytes()
        except Conflict as conflict:
            if conflict.code == 'template_base':
                raise
            raise Conflict(relative, 'Template source invalid: ' + conflict.reason) from conflict
        except OSError as exc:
            raise Conflict(relative, 'Template source unreadable: ' + (exc.strerror or str(exc))) from exc
        if not data:
            raise Conflict(relative, 'Template source is empty')
        if fsafe.sha256(data) != ctx.sync_file[relative]['sha256']:
            raise Conflict(relative, 'Template source differs from its recorded hash' + HASH_HINT, 'template_base')
        result[relative] = (data, ctx.sync_file[relative]['executable'])
    unlisted = []
    for current, directories, names in (os.walk(ctx.source_root / ctx.template_base) if base.is_dir() else ()):
        for entry in [*directories, *names]:
            full = Path(current) / entry
            relative = str(full.relative_to(ctx.source_root / ctx.template_base))
            if full.is_symlink():
                raise Conflict(relative, 'Symlink in the template base', 'template_base')
            if entry in names and relative not in ctx.sync_file:
                unlisted.append(relative)
    if unlisted:
        raise Conflict('.', 'Unlisted file(s) in sync/: ' + ', '.join(sorted(unlisted)) + HASH_HINT, 'template_base')
    return result
