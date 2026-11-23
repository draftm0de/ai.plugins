"""The marketplace association of a plugin (read-only report)."""
import os
from pathlib import Path
from . import evidence_files
from . import fsafe
from .constants import Conflict


def resolve_association(ctx, root, artifact):
    """Look at the local marketplace checkout of a plugin. Returns (state, path, identity): state is ok, path_missing,
    path_invalid, mismatch (identity of the checkout or the catalog entry of the plugin differs) or unsupported;
    identity is the {name} the checkout declares (None unless readable)."""
    local, value = evidence_files.read_local(ctx, root)
    if local == 'missing':
        return 'path_missing', None, None
    if local == 'unsupported':
        return 'unsupported', None, None
    checkout = Path(os.path.abspath(Path(value).expanduser() if Path(value).is_absolute() else root / value))
    try:
        if not checkout.is_dir() or fsafe.check_chain(checkout, 'marketplace.json', 'file') == 'missing':
            return 'path_invalid', value, None
        market = fsafe.strict_json(fsafe.read_regular(checkout, 'marketplace.json').decode('utf-8'))
    except (Conflict, ValueError, UnicodeDecodeError, OSError):
        return 'path_invalid', value, None
    if not (isinstance(market, dict) and isinstance(market.get('name'), str) and isinstance(market.get('plugins'), list)):
        return 'path_invalid', value, None
    identity = {'name': market['name']}
    try:
        plugin_repo = fsafe.strict_json(fsafe.read_regular(root, 'plugin.json').decode('utf-8')).get('repository')
    except (Conflict, ValueError, UnicodeDecodeError, OSError, AttributeError):
        plugin_repo = None
    entry = next((e for e in market['plugins'] if isinstance(e, dict) and e.get('name') == artifact), None)
    if entry is None or not isinstance(plugin_repo, str) or not isinstance(entry.get('repository'), str) \
            or evidence_files.norm_repo(entry['repository']) != evidence_files.norm_repo(plugin_repo):
        return 'mismatch', value, identity
    return 'ok', value, identity


def association_report(ctx, root, evidence):
    """Read-only hint for the status answer; never a gate for ready."""
    if evidence is None or not ctx.kinds[evidence['kind']]['requires_marketplace']:
        return None
    state, path, identity = resolve_association(ctx, root, evidence['artifact'])
    declared = evidence['marketplace']
    if state == 'ok' and identity['name'] != declared['name']:
        state = 'mismatch'
    return {'marketplace': declared, 'path': path, 'state': state}
