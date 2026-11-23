"""Target folder detection and classification of unconfigured folders."""
import os
from pathlib import Path
from . import evidence_files
from . import fsafe
from . import preferences
from .constants import BASE_ENTRIES, Conflict, LANGUAGE_PATH, NAME, OLD_LOCK_PATH, PROJECT_ENTRIES


def skeleton_paths(ctx):
    files = set(ctx.managed_files)
    directories = {d for f in ctx.managed_files for d in (f.rsplit('/', i)[0] for i in range(1, f.count('/') + 1))}
    return files, directories


def classify_unconfigured(ctx, root):
    """Accept a folder without plugin.json only if it holds nothing but metadata and skeleton paths.

    .git and .idea are only checked for being real directories, never opened or read."""
    names = sorted(os.listdir(root))
    fresh_entries = set(BASE_ENTRIES) | {path.split('/')[0] for path in ctx.managed_files}
    others = [n for n in names if n not in fresh_entries]
    files, directories = skeleton_paths(ctx)
    for top in ('scripts', 'skills'):  # walk only the skeleton folders; unknown names are foreign content
        if top in names and os.path.isdir(root / top) and not os.path.islink(root / top):
            stack = [top]
            while stack:
                current = stack.pop()
                for child in sorted(os.listdir(root / current)):
                    relative = current + '/' + child
                    if relative in directories and os.path.isdir(root / relative) and not os.path.islink(root / relative):
                        stack.append(relative)
                    elif relative not in files and relative not in directories:
                        others.append(relative)
                    elif relative in directories:
                        pass  # symlink or file where a folder belongs: reported by inspect()
    if others:
        raise Conflict('.', 'Folder has other content and is not an initializable plugin folder: ' + ', '.join(others),
                       'not_fresh', sorted(others))
    for entry in ('.git', '.idea'):
        if entry in names:
            fsafe.check_chain(root, entry, 'dir')
    if '.gitignore' in names:
        preferences.read_ignore(root)  # regular, non-symlink, UTF-8; content is preserved and only extended later
    if '.project' in names:
        fsafe.check_chain(root, '.project', 'dir')
        inner = sorted(os.listdir(root / '.project'))
        extra = [n for n in inner if n not in PROJECT_ENTRIES]
        if extra:
            raise Conflict('.project', 'Folder has other content and is not an initializable plugin folder: .project/'
                           + ', .project/'.join(extra), 'not_fresh', ['.project/' + n for n in extra])
        try:
            preferences.load_language_helper(ctx).preference(root)  # validates the stored preference without writing
        except (ValueError, OSError) as exc:
            raise Conflict(LANGUAGE_PATH, str(exc)) from exc
    return names


def product_name(root, filename):
    """Name of an existing root plugin.json/marketplace.json or None when absent."""
    if fsafe.check_chain(root, filename, 'file') == 'missing':
        return None
    try:
        manifest = fsafe.strict_json(fsafe.read_regular(root, filename).decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Conflict(filename, 'Invalid ' + filename + ': ' + str(exc)) from exc
    name = manifest.get('name') if isinstance(manifest, dict) else None
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise Conflict(filename, filename + ' needs a valid name')
    return name


def detect_target(ctx, target, allow_unconfigured=True):
    """Return (root, artifact name or None, state). state is the configured kind (plugin|marketplace) from the
    configuration evidence of the running plugin, otherwise 'unconfigured'. A root plugin.json/marketplace.json
    is a product, never evidence."""
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.is_symlink():
        raise Conflict('.', 'Target is a symlink; select the real directory')
    root = path.resolve()
    if not root.is_dir():
        raise Conflict('.', 'Target directory does not exist')
    if root == ctx.manager_root:
        raise Conflict('.', 'The embedded Plugin Manager is not a setup target')
    if fsafe.check_chain(root, OLD_LOCK_PATH, 'file') != 'missing':
        raise Conflict(OLD_LOCK_PATH, 'Unsupported former skeleton lock location; use ' + ctx.lock_path
                       + '. Existing data preserved, no migration', 'lock_format')
    evidence = evidence_files.read_evidence(ctx, root)
    products = {k: product_name(root, v['product']) for k, v in ctx.kinds.items() if v['product']}
    if evidence is None:
        ctx.use_kind(None)  # the skeleton depends on the kind, which only the configuration evidence names
        if all(name is None for name in products.values()):
            classify_unconfigured(ctx, root)
        return root, None, 'unconfigured'
    kind = evidence['kind']
    for other, name in products.items():
        if other != kind and name is not None and ctx.kinds[kind]['product']:
            raise Conflict(ctx.kinds[other]['product'], 'Configured as ' + kind + ', but the folder holds a ' + ctx.kinds[other]['product'], other)
    if kind == 'plugin' and products.get('plugin') == 'plugin-manager':
        raise Conflict('plugin.json', 'The embedded Plugin Manager is not a setup target')
    ctx.use_kind(kind)
    return root, evidence['artifact'], kind
