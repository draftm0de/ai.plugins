"""The writing style of the documentation (docs/style.md): created once, never changed (R38)."""
import os
from . import detection
from . import fsafe
from . import inspection
from . import reporting
from .constants import Conflict


def create(ctx, target, content=None):
    """Create docs/style.md from the template of the kind, or with the given text of the person; never overwrites."""
    root, name, state = detection.detect_target(ctx, target, allow_unconfigured=True)
    if state == 'unconfigured':
        raise Conflict('.', 'Configure first: the style belongs to the configured kind', 'not_configured')
    info = inspection.style_state(ctx, root)
    if info['present']:
        raise Conflict(info['path'], 'The file exists already; it is never changed')
    if not info['required']:
        raise Conflict(info['path'], 'This kind has no template for it')
    if content is None:
        data = (ctx.source_root / ctx.template_base.rsplit('/', 1)[0] / 'seed' / info['path']).read_bytes()
    else:
        if not content.strip():
            raise Conflict(info['path'], 'The text is empty')
        data = (content.rstrip('\n') + '\n').encode('utf-8')
    fsafe.check_chain(root, 'docs', 'dir')
    created = []
    fsafe.ensure_directory(root / 'docs', created)
    if not fsafe.copy_new(root / info['path'], data, False):
        raise Conflict(info['path'], 'The file exists already; it is never changed')
    return {'operation': 'style', 'ok': True, 'target': str(root), 'plugin': name, 'created': [info['path']],
            'from_template': content is None, 'next': 'status', 'target_code_executed': False}
