"""Writes the configuration evidence after a passed configuration run."""
from datetime import datetime, timezone
import json
from . import associations
from . import detection
from . import fsafe
from . import skeleton
from .constants import Conflict, EVIDENCE_PATH, EVIDENCE_VERSION, LOCAL_PATH, NAME


def record(ctx, target, kind, artifact):
    """Write the configuration evidence after a successful configuration run (never earlier)."""
    root, name, state = detection.detect_target(ctx, target)
    if kind not in ctx.kinds or not NAME.fullmatch(artifact or ''):
        raise Conflict('.', 'kind must be a known kind and artifact a valid name', 'invalid_record')
    product_file = ctx.kinds[kind]['product']
    if product_file and detection.product_name(root, product_file) != artifact:
        raise Conflict(product_file, 'The root product file must exist and carry the name ' + artifact, 'product_missing')
    if kind == 'plugin' and artifact == 'plugin-manager':
        raise Conflict('plugin.json', 'The embedded Plugin Manager is not a setup target')
    if state != 'unconfigured' and (state, name) != (kind, artifact):
        raise Conflict(EVIDENCE_PATH.format(plugin=ctx.plugin), 'The workpackage is already configured differently', 'already_configured')
    identity = None
    if state == 'unconfigured' and ctx.kinds[kind]['requires_marketplace']:
        association, _, found = associations.resolve_association(ctx, root, artifact)
        if association != 'ok':
            raise Conflict(LOCAL_PATH.format(plugin=ctx.plugin), 'A plugin belongs to exactly one marketplace: associate first (association state: '
                           + association + '); nothing was written', 'association_missing')
        identity = found
    created_dirs, created_files, errors = [], [], []
    path = EVIDENCE_PATH.format(plugin=ctx.plugin)
    if state == 'unconfigured':
        body = (json.dumps({'schema_version': EVIDENCE_VERSION, 'plugin': ctx.plugin, 'kind': kind, 'artifact': artifact,
                            'configured_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'marketplace': identity}, indent=2) + '\n').encode()
        try:
            skeleton.ensure_plugin_dir(ctx, root, created_dirs)
            if not fsafe.replace_if_unchanged(root / path, body, 0o666 & ~fsafe.current_umask(), None):
                raise OSError('Evidence appeared meanwhile; nothing was overwritten')
            created_files.append(path)
        except (OSError, ValueError) as exc:
            errors.append('Write failed: ' + str(exc))
    return {'operation': 'record', 'ok': not errors, 'state': kind if not errors else state, 'target': str(root),
            'plugin': artifact, 'conflicts': [], 'errors': errors,
            'created': {'files': created_files, 'directories': [str(d.relative_to(root)) for d in created_dirs]},
            'next': 'stop' if errors else 'status', 'target_code_executed': False}
