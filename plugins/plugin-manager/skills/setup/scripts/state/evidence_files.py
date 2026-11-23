"""Configuration evidence (config.json) and the local marketplace path (local.json)."""
from . import fsafe
from .constants import Conflict, EVIDENCE_KEYS, EVIDENCE_PATH, EVIDENCE_VERSION, LOCAL_KEYS, LOCAL_PATH, NAME, TIMESTAMP


def read_evidence(ctx, root):
    """Valid configuration evidence of the running plugin or None; anything else is rejected, never migrated."""
    path = EVIDENCE_PATH.format(plugin=ctx.plugin)
    if fsafe.check_chain(root, path, 'file') == 'missing':
        return None
    try:
        data = fsafe.strict_json(fsafe.read_regular(root, path).decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Conflict(path, 'Invalid configuration evidence: ' + str(exc)) from exc
    if not (isinstance(data, dict) and set(data) == EVIDENCE_KEYS and type(data['schema_version']) is int
            and data['schema_version'] == EVIDENCE_VERSION and data['plugin'] == ctx.plugin and isinstance(data['kind'], str)
            and isinstance(data['artifact'], str) and NAME.fullmatch(data['artifact'])
            and isinstance(data['configured_at'], str) and TIMESTAMP.fullmatch(data['configured_at'])):
        raise Conflict(path, 'Unsupported configuration evidence (schema_version ' + str(EVIDENCE_VERSION) + ' with plugin, kind, artifact, '
                       'UTC configured_at and marketplace); existing data preserved, no migration', 'config_format')
    if data['kind'] not in ctx.kinds:
        raise Conflict(path, 'Template base is missing for kind ' + repr(data['kind']) + ' (no manifests/<kind>.json)', 'template_base')
    identity = data['marketplace']
    if ctx.kinds[data['kind']]['requires_marketplace']:
        valid = isinstance(identity, dict) and set(identity) == {'name'} and isinstance(identity['name'], str) and NAME.fullmatch(identity['name'])
        message = 'A plugin belongs to exactly one marketplace: marketplace {name} is required for kind ' + data['kind']
    else:
        valid, message = identity is None, 'marketplace must be null for kind ' + data['kind']
    if not valid:
        raise Conflict(path, 'Unsupported configuration evidence: ' + message + '; existing data preserved, no migration', 'config_format')
    return data


def norm_repo(value):
    text = value.strip().rstrip('/')
    text = text[:-4] if text.endswith('.git') else text
    return text.rstrip('/').lower()


def read_local(ctx, root):
    """(state, path): the ignored local.json of the running plugin. state is missing, unsupported or ok."""
    path = LOCAL_PATH.format(plugin=ctx.plugin)
    try:
        if fsafe.check_chain(root, path, 'file') == 'missing':
            return 'missing', None
        data = fsafe.strict_json(fsafe.read_regular(root, path).decode('utf-8'))
    except (Conflict, ValueError, UnicodeDecodeError):
        return 'unsupported', None
    if not (isinstance(data, dict) and set(data) == LOCAL_KEYS and type(data['schema_version']) is int and data['schema_version'] == 1
            and isinstance(data['marketplace_path'], str) and data['marketplace_path'].strip() != ''):
        return 'unsupported', None
    return 'ok', data['marketplace_path']
