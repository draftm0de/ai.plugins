#!/usr/bin/env python3
"""Create separate repositories and associate plugins with their one marketplace. Never commit or publish."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
SKILL = Path(__file__).resolve().parents[1]


def strict_json(text):
    """Reject ambiguous or non-round-trippable JSON before planning writes."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field: ' + key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Invalid JSON numeric constant: ' + value)
    def finite_number(value):
        import math
        from decimal import Decimal
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Invalid JSON numeric constant: ' + value)
        if Decimal(value) != Decimal(str(number)):
            raise ValueError('Unsupported JSON numeric precision: ' + value)
        return number
    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant, parse_float=finite_number)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()


def safe_path(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink target requires explicit review: ' + str(path))
    return path


def read(path, default=None):
    path = safe_path(path)
    if not path.exists() and default is not None:
        return default
    value = strict_json(path.read_text())
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object: ' + str(path))
    return value


def repository_url(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('A GitHub address is needed, for example https://github.com/<owner>/<name>.git')
    value = value.strip().removesuffix('.git')
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', value)
    if not match:
        raise ValueError('The address ' + value + ' is not a plain GitHub address. Use the form https://github.com/<owner>/<name>.git, without a user name or password.')
    return 'https://github.com/' + match[1]


def git(root, *args):
    """Run Git in `root`; returns its output, or None when Git exits with an error. A missing Git is a plain message."""
    try:
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except FileNotFoundError:
        raise ValueError('Git is not installed or cannot be found. Install Git and try again.') from None
    except subprocess.CalledProcessError:
        return None


NOT_A_REPOSITORY = 'The folder {root} is not a Git repository. In your IDE (for example VS Code) or in a terminal, run `git init` in that folder.'


def git_root(root):
    """The folder must itself be the root of a Git repository (a marketplace needs no origin)."""
    actual = git(root, 'rev-parse', '--show-toplevel')
    if actual is None:
        raise ValueError(NOT_A_REPOSITORY.format(root=root))
    if Path(actual).resolve() != root.resolve():
        raise ValueError('The folder ' + str(root) + ' lies inside the Git repository ' + actual + '. Choose the folder that is itself the repository.')


def git_tracked(root, path):
    """Whether Git tracks anything at `path` in the repository at `root`."""
    listing = git(root, 'ls-files', '--', path)
    if listing is None:
        raise ValueError(NOT_A_REPOSITORY.format(root=root))
    return bool(listing)


def git_repository(root, supplied=None):
    git_root(root)
    configured = git(root, 'config', '--get', 'remote.origin.url')
    if not configured:
        raise ValueError('The folder ' + str(root) + ' has no GitHub address yet. In your IDE or in a terminal, run '
                         '`git remote add origin https://github.com/<owner>/<name>.git` in that folder. The repository does not have to exist yet.')
    origin = repository_url(configured)
    if supplied and repository_url(supplied) != origin:
        raise ValueError('The given address ' + supplied + ' differs from the GitHub address of the folder (' + origin + ').')
    return origin


def identity(name, display):
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Technical name is required in lowercase kebab-case')
    if not isinstance(display, str) or not display.strip():
        raise ValueError('Display name is required separately from technical name')


def apply(files, replace=()):
    """Preflight the whole change, preserve foreign files, roll back on write failure."""
    previous = {}
    changes = {}
    for path, content in files.items():
        path = safe_path(path)
        if path.exists() and not path.is_file():
            raise ValueError('Not a regular file: ' + str(path))
        before = path.read_bytes() if path.exists() else None
        if before == content:
            continue
        if before is not None and path not in replace:
            raise ValueError('Existing content differs; review before replacing: ' + str(path))
        previous[path] = before
        changes[path] = content
    written = []
    try:
        for path, content in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                temp = Path(handle.name)
                handle.write(content)
            try:
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
            written.append(path)
    except OSError:
        for path in reversed(written):
            if previous[path] is None:
                path.unlink()
            else:
                path.write_bytes(previous[path])
        raise
    return [str(p) for p in changes]


# Rules of the plugin template that only newly generated plugin repositories receive.
PLUGIN_ONLY_IGNORES = frozenset({'/.project/operator.json'})
# Rules every plugin repository needs where the machine-specific marketplace path is stored (never committed).
PLUGIN_REPO_IGNORES = frozenset({'/.project/plugins/*/local.json'})
OWNER = 'plugin-manager'  # the running plugin that owns the workpackage evidence of the plugin repositories
EVIDENCE_FILE = '.project/plugins/{plugin}/config.json'
LOCAL_FILE = '.project/plugins/' + OWNER + '/local.json'


def ignore_file(root, new_plugin=False, plugin_repo=False):
    path = safe_path(root/'.gitignore')
    text = path.read_text() if path.exists() else ''
    for pattern in (SKILL/'templates/plugin/seed/gitignore.txt').read_text().splitlines():
        if not pattern or pattern.startswith('#'):
            continue
        if pattern in PLUGIN_ONLY_IGNORES and not new_plugin:
            continue
        if pattern in PLUGIN_REPO_IGNORES and not plugin_repo:
            continue
        if pattern not in text.splitlines():
            text = text.rstrip() + '\n' + pattern + '\n'
    # Evaluate the proposed repository rules with Git before writing either repo.
    # Global excludes must not mask unsafe committed rules on another machine.
    from repository_policy import git as isolated_git
    with tempfile.TemporaryDirectory(prefix='plugin-ignore-') as directory:
        shadow = Path(directory)
        if isolated_git(shadow, 'init', '--quiet', '--template=').returncode:
            raise ValueError('Cannot evaluate proposed Git ignore rules')
        (shadow/'.gitignore').write_text(text)
        nested = safe_path(root/'.local/.gitignore')
        if nested.exists():
            (shadow/'.local').mkdir()
            (shadow/'.local/.gitignore').write_bytes(nested.read_bytes())
        probe = LOCAL_FILE if plugin_repo else '.local/marketplace.json'
        result = isolated_git(shadow, 'check-ignore', '--no-index', '--', probe)
        if result.returncode not in (0, 1):
            raise ValueError('Cannot evaluate proposed Git ignore rules')
        if probe not in result.stdout.splitlines():
            raise ValueError('Ineffective Git ignore rules for ' + probe + ' in ' + str(root) +
                             '; review .gitignore and .local/.gitignore before writing associations')
    return path, text.encode()


def catalog_files(root, config):
    engine = module(SKILL/'templates/marketplace/sync/scripts/marketplace.py', 'catalog_template')
    return {root/path: encode(data) for path, data in engine.expected(root, config).items()}


def template_source(kind, relative):
    """Template file of a kind: synced files live in sync/, files created once in seed/."""
    for part in ('sync', 'seed'):
        path = SKILL/'templates'/kind/part/relative
        if path.is_file():
            return path
    raise FileNotFoundError(f'No template {relative} for kind {kind}')


def template_files(kind, root):
    files = {}
    for part in ('sync', 'seed'):
        folder = SKILL/'templates'/kind/part
        files.update({root/p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    return files


def create_marketplace(root, name=None, display_name=None, owner=None):
    root = safe_path(root)
    git_root(root)
    if (root/'plugin.json').exists():
        raise ValueError('A plugin repository cannot become a marketplace')
    existing = read(root/'marketplace.json', {})
    name = name or existing.get('name')
    display_name = display_name or existing.get('displayName')
    identity(name, display_name)
    publisher = {'name': owner} if owner else existing.get('owner')
    if not publisher or not publisher.get('name'):
        raise ValueError('Confirmed marketplace owner is required; Git author is not a publisher decision')
    if existing and (existing['name'] != name or existing['displayName'] != display_name or existing['owner'] != publisher):
        raise ValueError('Existing marketplace identity conflicts; creation does not migrate it')
    config = existing or {'name': name, 'displayName': display_name, 'owner': publisher, 'plugins': []}
    files = template_files('marketplace', root)
    # Synced skeleton files (manifests/marketplace.sync.json) belong to the skeleton and sync flows: an existing regular
    # file is neither judged nor replaced here, a missing one is created.
    synced = read(SKILL/'manifests/marketplace.sync.json')['files']
    for relative in synced:
        existing_file = root/relative
        if existing_file.is_file() and not existing_file.is_symlink():
            files.pop(existing_file, None)
    files[root/'marketplace.json'] = encode(config)
    files.update(catalog_files(root, config))
    # Keep existing project prose and licensing untouched.
    for lang, filename in (('de', 'README.md'), ('en', 'README.en.md')):
        if not (root/filename).exists():
            text = (f'# {display_name}\n\nMarketplace `{name}`\n\n' +
                ('Plugin-Repositories werden in `marketplace.json` eingetragen. Lokale Pfade stehen ausschließlich in `.local/marketplace.json`.\n\n' if lang == 'de' else 'Plugin repositories are registered in `marketplace.json`. Local paths belong only in `.local/marketplace.json`.\n\n') +
                '```sh\npython3 -B scripts/verify.py --source .\npython3 -B scripts/marketplace.py check\nmake install-local TARGET=claude\n```\n\n' +
                ('Ein frischer Clone benötigt für lokale Installation zuerst Checkout-Zuordnungen über die Plugin-Zuordnung von plugin-manager. local-marketplace.example.json ist nur eine optionale manuelle Kopiervorlage; nur .local/marketplace.json wird zur Laufzeit gelesen und bleibt uncommitted. Snapshots verwenden den aktuellen Checkout einschließlich uncommitteter Änderungen auf jedem Branch. Nach Änderungen oder Branchwechsel install-local und eine neue Host-Sitzung; kein Commit/Push/PR und kein Marketplace pro Branch. [Voraussetzungen](docs/prerequisites.md): Git und Python 3.10+, Make optional, Host-CLI nur für automatische lokale Installation. Strukturprüfung ist keine GitHub-/GUI-Abnahme.\n' if lang == 'de' else 'A fresh clone needs checkout associations through the plugin association of plugin-manager before local installation. local-marketplace.example.json is only an optional manual template; only .local/marketplace.json is read at runtime and stays uncommitted. Snapshots use the current checkout including uncommitted edits on any branch. After edits or branch switches run install-local and open a new host session; no commit/push/PR or per-branch marketplace. [Prerequisites](docs/prerequisites.md): Git and Python 3.10+, optional Make, host CLI only for automatic local installation. Structural verification is not GitHub/GUI acceptance.\n'))
            files[root/filename] = text.encode()
    ignore, content = ignore_file(root); files[ignore] = content
    return {'action': 'create-marketplace', 'changed': apply(files, [ignore]), 'published': False}


def checkout_path(base, value):
    path = Path(value).expanduser()
    return Path(os.path.abspath(path if path.is_absolute() else base/path))


def plugin_local_association(plugin_root):
    """The one marketplace a plugin belongs to on this machine: relative path from the ignored local.json, or None.
    Only {"schema_version": 1, "marketplace_path": "<path>"} is supported; the former plugin-side .local/marketplace.json
    is neither read nor migrated."""
    path = plugin_root/LOCAL_FILE
    if not path.exists():
        return None
    local = read(path)
    if (set(local) != {'schema_version', 'marketplace_path'} or type(local['schema_version']) is not int or local['schema_version'] != 1
            or not isinstance(local['marketplace_path'], str) or not local['marketplace_path'].strip()):
        raise ValueError('Unsupported plugin-local association format in ' + str(path) + ': only {"schema_version": 1, '
                         '"marketplace_path": "<path>"} is supported (a plugin belongs to exactly one marketplace); '
                         'existing data preserved, no migration')
    return local['marketplace_path']


def market_identity(path):
    config = read(path/'marketplace.json')
    if not isinstance(config.get('name'), str) or not config['name'].strip():
        raise ValueError('The marketplace needs a name in marketplace.json to be associated: ' + str(path/'marketplace.json'))
    return {'name': config['name']}


def plugin_entry(manifest, url):
    return {'name': manifest['name'],
            'displayName': manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName', manifest['name']),
            'description': manifest['description'], 'repository': url + '.git'}


def association_files(plugin_root, market, manifest, new_plugin=False, allow_change=False):
    market = safe_path(market)
    git_root(market)
    verifier = module(SKILL/'scripts/verify.py', 'trusted_verify')
    verifier.marketplace(market)
    market_identity(market)  # the name at the root, checked before any file of this change is written
    config = read(market/'marketplace.json')
    name = manifest['name']
    url = repository_url(manifest['repository'])
    entry = plugin_entry(manifest, url)
    found = False
    for index, old in enumerate(config['plugins']):
        if old.get('name') == name:
            if repository_url(old['repository']) != url:
                raise ValueError('Plugin identity already refers to a different repository')
            config['plugins'][index] = entry; found = True
        elif old.get('repository') and repository_url(old['repository']) == url:
            raise ValueError('Repository is already registered with another plugin identity')
    if not found:
        config['plugins'].append(entry)
    for checkout, tracked in ((market, '.local'), (plugin_root, LOCAL_FILE)):
        if git_tracked(checkout, tracked):
            raise ValueError('Local configuration is tracked; review before writing private checkout mappings')
    previous = plugin_local_association(plugin_root)
    if previous and not allow_change and checkout_path(plugin_root, previous).resolve() != market.resolve():
        raise ValueError('Plugin is already associated with another marketplace (' + previous + '); a plugin belongs to exactly one marketplace, use associate to change it')
    local = read(market/'.local/marketplace.json', {})
    sources = local.setdefault('sources', {})
    if name in sources:
        known = checkout_path(market, sources[name])
        if known.resolve() != plugin_root.resolve():
            raise ValueError('Existing local checkout differs; review this mapping before replacement')
    sources[name] = os.path.relpath(plugin_root, market)
    relative = os.path.relpath(market, plugin_root)
    files = {market/'marketplace.json': encode(config), market/'.local/marketplace.json': encode(local),
             plugin_root/LOCAL_FILE: encode({'schema_version': 1, 'marketplace_path': relative})}
    files.update(catalog_files(market, config))
    for root, is_plugin in ((market, False), (plugin_root, True)):
        path, content = ignore_file(root, new_plugin=new_plugin and is_plugin, plugin_repo=is_plugin); files[path] = content
    return files


def release_old_marketplace(old, plugin_root, manifest):
    """Files that remove exactly this plugin from its previous marketplace checkout (name and repository must match)."""
    git_root(old)
    verifier = module(SKILL/'scripts/verify.py', 'trusted_verify')
    verifier.marketplace(old)
    if git_tracked(old, '.local'):
        raise ValueError('Local configuration is tracked; review before writing private checkout mappings')
    config = read(old/'marketplace.json')
    name, url = manifest['name'], repository_url(manifest['repository'])
    kept = []
    for entry in config['plugins']:
        if entry.get('name') == name:
            if repository_url(entry['repository']) != url:
                raise ValueError('Previous marketplace lists this plugin name for a different repository; review it there first')
            continue
        kept.append(entry)
    config['plugins'] = kept
    files = {old/'marketplace.json': encode(config)}
    local = read(old/'.local/marketplace.json', {})
    sources = local.get('sources', {})
    if name in sources and checkout_path(old, sources[name]).resolve() == plugin_root.resolve():
        del sources[name]
        files[old/'.local/marketplace.json'] = encode(local)
    files.update(catalog_files(old, config))
    return files


def state_helper():
    """The setup state package (skills/setup/scripts/state), imported from its own folder like its command line does."""
    scripts = SKILL.parent / 'setup' / 'scripts'
    loaded = sys.modules.get('state')
    if loaded is not None and Path(getattr(loaded, '__file__', '') or '').resolve().parent != scripts / 'state':
        for name in [n for n in sys.modules if n == 'state' or n.startswith('state.')]:
            del sys.modules[name]  # another package of that name was imported first: use this plugin's own
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import state
    return state


def load_evidence(root, plugin):
    """Valid configuration evidence (schema 2) of the running plugin through the central helper, as ValueError."""
    helper = state_helper()
    from state import evidence_files
    try:
        ctx = helper.Context(plugin)
        evidence = evidence_files.read_evidence(ctx, root)
    except helper.Conflict as conflict:
        raise ValueError(conflict.reason + ' (' + str(conflict.path) + ')') from conflict
    return evidence, ctx.kinds


def associate(root, marketplace, repository=None, drop_missing_old=False, plugin=OWNER):
    """Set or change the one marketplace a plugin belongs to, in one rollback-capable transaction.

    The identity (name, repository) goes into the committed config.json, the path of the checkout into the ignored
    local.json. Nothing is committed, pushed, installed or published."""
    root = safe_path(root); market = safe_path(marketplace)
    origin = git_repository(root, repository)
    if root == market or root.is_relative_to(market) or market.is_relative_to(root):
        raise ValueError('Use separate plugin and marketplace repositories')
    evidence, kinds = load_evidence(root, plugin)
    if evidence is None:
        raise ValueError('Configure first: this workpackage has no configuration evidence for ' + plugin + ' (flows/configure.md)')
    if not kinds[evidence['kind']]['requires_marketplace']:
        raise ValueError('Only a plugin belongs to a marketplace; this workpackage is configured as ' + evidence['kind'])
    verifier = module(SKILL/'scripts/verify.py', 'trusted_verify')
    verifier.plugin(root)
    manifest = read(root/'plugin.json')
    if repository_url(manifest['repository']) != origin:
        raise ValueError('Plugin manifest conflicts with Git origin')
    if manifest['name'] != evidence['artifact']:
        raise ValueError('plugin.json carries another name than the configuration evidence (' + evidence['artifact'] + ')')
    declared = evidence['marketplace']
    target = market_identity(market)
    same = target['name'] == declared['name']
    previous = plugin_local_association(root)
    old = None
    # the same checkout under a new name (the marketplace was renamed, R24): found through the path the plugin already records
    renamed = (not same) and previous is not None and checkout_path(root, previous).resolve() == market.resolve()
    if renamed:  # the same marketplace under a new name (R24): only the identity in config.json follows, no catalog change
        url = repository_url(manifest['repository'])
        verifier.marketplace(market)
        if not any(e.get('name') == manifest['name'] and e.get('repository') and repository_url(e['repository']) == url
                   for e in read(market/'marketplace.json')['plugins']):
            raise ValueError('The renamed marketplace does not list this plugin (name and repository); it has to be listed there first')
        files = {root/LOCAL_FILE: encode({'schema_version': 1, 'marketplace_path': os.path.relpath(market, root)})}
    else:
        if not same:  # the plugin leaves its marketplace: the old catalog entry has to go with it
            if previous:
                candidate = checkout_path(root, previous)
                if (candidate/'marketplace.json').is_file() and market_identity(candidate)['name'] == declared['name']:
                    old = candidate
            if old is None and not drop_missing_old:
                raise ValueError('The previous marketplace ' + declared['name'] + ' is not available locally, so its catalog entry cannot be removed; '
                                 'restore its checkout at ' + (previous or '(no local path recorded)') + ', or confirm --drop-missing-old to release only the local reference')
            if old is not None and (old.resolve() == root.resolve() or old.resolve().is_relative_to(root.resolve())):
                raise ValueError('Use separate plugin and marketplace repositories')
        files = association_files(root, market, manifest, allow_change=True)
        if old is not None:
            files.update(release_old_marketplace(old, root, manifest))
    updated = dict(evidence); updated['marketplace'] = target
    files[root/EVIDENCE_FILE.format(plugin=plugin)] = encode(updated)
    changed = apply(files, list(files))
    return {'action': 'associate', 'changed': changed, 'published': False,
            'from': {'name': declared['name'], 'path': previous},
            'to': {'name': target['name'], 'path': os.path.relpath(market, root)},
            'old_catalog_entry_remains': (not same) and (not renamed) and old is None, 'renamed': renamed,
            'next': 'Committed files changed and are unversioned: config.json of the plugin, marketplace.json and the host catalogs of the marketplaces involved. '
                    'Review them in their repositories and publish them through publish. Nothing was committed, pushed, installed or published.'}


def complete_skeleton_documentation(stage, title):
    """Replace the scaffold pages of a newly staged repository by the finished skeleton pages of
    templates/skeleton-docs (real Markdown, same layout as templates/); never touches existing user documentation."""
    from documentation import language_policy, page_layout, template_text, validate
    policy = language_policy(stage)
    for relative, (template, _, _) in page_layout(policy).items():
        text = template_text(template, policy, base=SKILL/'templates/skeleton-docs')
        (stage/relative).write_text(text.replace('{{TITLE}}', title), encoding='utf-8')
    errors = validate(stage)
    if errors:
        raise ValueError('Skeleton documentation validation failed: ' + '; '.join(errors))


def creation_checks(root, market, license_decision=None):
    """Read actual output using trusted helpers, without executing target code."""
    from documentation import validate
    from verify import verify
    checks = {}
    for label, target in (('plugin', root), ('marketplace', market)):
        try:
            checks[label] = verify(target, kind=label)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            checks[label] = {'structure_valid': False, 'error': str(exc)}
    try:
        errors = validate(root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        errors = [str(exc)]
    checks['documentation'] = {'valid': not errors, 'errors': errors}
    checks['status'] = ('passed' if not errors and all(checks[k]['structure_valid']
                        for k in ('plugin', 'marketplace')) else 'needs_attention')
    checks['licensing'] = 'not_assessed; report the separately confirmed decision and actual license files'
    if license_decision is not None:
        from licensing import check
        checks['licensing'] = check(root, license_decision)
        if not checks['licensing']['valid']:
            checks['status'] = 'needs_attention'
    checks['functional_acceptance'] = 'pending'
    checks['tests'] = 'not_run'
    checks['host_acceptance'] = 'not_run'
    return checks


def create_plugin(root, marketplace, *, name=None, display_name=None, description=None, repository=None, author=None, languages=None, default_language=None, skeleton=False, license=None, license_file=None, copyright_year=None, copyright_holder=None):
    root = safe_path(root)
    if any((root/item).exists() or (root/item).is_symlink() for item in ('plugin.json', 'marketplace.json')):
        raise ValueError('Product already exists; an existing plugin is not created again (associate changes its marketplace)')
    if not skeleton:
        raise ValueError('create --kind plugin supports only --skeleton; skill import is unsupported')
    market = safe_path(marketplace)
    if root == market or root.is_relative_to(market) or market.is_relative_to(root):
        raise ValueError('Use separate plugin and marketplace repositories')
    identity(name, display_name)
    description = description or "Unimplemented plugin skeleton; domain requirements are pending."
    from licensing import plan, document
    license_decision = plan(root, license, license_file, copyright_year, copyright_holder)
    if not root.exists():
        url = repository_url(repository)
        root.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'init.templateDir=', 'clone', '--', url + '.git', str(root)], check=True)
    origin = git_repository(root, repository)
    if (root/'plugin.json').exists() or (root/'marketplace.json').exists():
        raise ValueError('Product already exists; an existing plugin is not created again (associate changes its marketplace)')
    for obsolete in ('.claude/skills', '.agents/skills', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', '.codex-plugin/marketplace.json'):
        if (root/obsolete).exists() or (root/obsolete).is_symlink():
            raise ValueError('Unsupported host-local skill layout: ' + obsolete)
    if not description or not author:
        raise ValueError('Confirmed description and publisher required; do not invent product facts')
    from documentation import language_policy
    policy = language_policy(root, languages, default_language)
    languages = policy['languages']
    default_language = policy['default_language']
    # Build in scratch first; inspect all collisions before writing either repository.
    from plugin_audit import scaffold_plugin
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory).resolve()/'plugin'
        stub = Path(directory).resolve()/'source'/name
        stub.mkdir(parents=True)
        (stub/"SKILL.md").write_text("---\nname: " + name + "\ndescription: Unimplemented plugin skeleton; no domain behavior is available.\n---\n\n# Plugin skeleton\n\nBefore any interaction, read and follow `../_shared/references/operator-language.md`.\n\n<!-- plugin-skeleton: unimplemented -->\n\nThis is a nonfunctional development skeleton. Do not perform domain actions or claim capabilities. Read SCOPE.md in the source repository and clarify requirements before implementing. Remove the skeleton marker only after implementing and reviewing the agreed behavior.\n")
        scaffold_plugin(stub, stage, languages, default_language, origin, author, name)
        manifest = read(stage/'plugin.json')
        manifest['description'] = description
        manifest['extensions']['com.openai'] = {'interface': {'displayName': display_name}}
        if license_decision['identifier']:
            manifest['license'] = license_decision['identifier']
            (stage/license_decision['file']).write_bytes(license_decision['content'])
        (stage/'plugin.json').write_bytes(encode(manifest))
        engine = module(SKILL/'templates/plugin/sync/scripts/plugin.py', 'trusted_payload')
        for path, data in engine.repository_files(manifest).items():
            (stage/path).write_bytes(encode(data))
        complete_skeleton_documentation(stage, display_name)
        document(stage, license_decision)
        files = {root/p.relative_to(stage): p.read_bytes() for p in stage.rglob('*') if p.is_file()}
        # Managed skeleton files (common list of the kind manifest) belong to the skeleton and sync flows: an existing
        # regular file is never judged or replaced here, a missing one is created.
        common = json.loads((SKILL/'manifests/plugin.sync.json').read_text(encoding='utf-8'))['files']
        for relative in common:
            existing = root/relative
            if existing.is_file() and not existing.is_symlink():
                files.pop(existing, None)
        # Existing prose and licenses remain canonical; docs action can later merge them.
        for path in list(files):
            if (path.exists() and path not in (root/'docs/architecture.md', root/'docs/prerequisites.md', root/'docs/license.md')
                    and (path.name.startswith('README') or path.is_relative_to(root/'docs'))):
                del files[path]
        association = association_files(root, market, manifest, new_plugin=True)
        files.update(association)
        changes = apply(files, association.keys())
    checks = creation_checks(root, market, license_decision)
    next_step = 'Confirm SCOPE.md, implement agreed behavior under skills/, add tests, then run verify --review. No functional acceptance is claimed.'
    if checks['status'] != 'passed':
        next_step = 'Resolve the reported creation checks before claiming completion. ' + next_step
    return {'action': 'create-plugin', 'changed': changes, 'repository': origin, 'published': False,
            'implementation_status': 'skeleton', 'checks': checks, 'next': next_step}


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Requires Git and Python 3.10+; Make is optional. associate sets or changes the one marketplace of a plugin; the example JSON is only a manual template. No automatic tool installation.')
    sub = parser.add_subparsers(dest='action', required=True)
    create = sub.add_parser('create', help='Create a marketplace or a plugin skeleton (--kind)')
    create.add_argument('--kind', required=True, choices=('marketplace', 'plugin'))
    create.add_argument('--root', type=Path, default=Path.cwd(), help='User project root, never manager installation')
    create.add_argument('--repository')
    create.add_argument('--name'); create.add_argument('--display-name')
    create.add_argument('--owner', help='kind marketplace only')
    create.add_argument('--marketplace', type=Path, help='kind plugin only (required): local checkout of the one marketplace the plugin belongs to')
    create.add_argument('--skeleton', action='store_true', help='kind plugin only: nonfunctional skeleton with pending SCOPE.md; no invented domain content')
    create.add_argument('--description'); create.add_argument('--author')
    create.add_argument('--languages', nargs='+', choices=['de','en'])
    create.add_argument('--default-language', choices=['de','en'])
    create.add_argument('--license', help='kind plugin only, required for new plugins: confirmed identifier, or deferred after explicit user choice')
    create.add_argument('--license-file', type=Path, help='Confirmed complete license text; copied unchanged')
    create.add_argument('--copyright-year', help='Confirmed MIT copyright year or year range')
    create.add_argument('--copyright-holder', help='Confirmed MIT rights holder, never inferred from author')
    associate_parser = sub.add_parser('associate', help='Set or change the one marketplace of a plugin')
    associate_parser.add_argument('--root', type=Path, default=Path.cwd(), help='User project root, never manager installation')
    associate_parser.add_argument('--repository')
    associate_parser.add_argument('--marketplace', type=Path, required=True, help='Local checkout of the one marketplace the plugin belongs to')
    associate_parser.add_argument('--plugin', default=OWNER, help='Running plugin that owns the workpackage evidence')
    associate_parser.add_argument('--drop-missing-old', action='store_true', help='Release only the local reference when the previous marketplace checkout is gone (its catalog entry then remains there)')
    parsed, unknown = parser.parse_known_args()
    args = vars(parsed); action = args.pop('action')
    if unknown:
        parser.error('unrecognized arguments: ' + ' '.join(unknown))
    if action == 'create':
        kind = args.pop('kind')
        plugin_only = ('marketplace', 'skeleton', 'description', 'author', 'languages', 'default_language', 'license',
                       'license_file', 'copyright_year', 'copyright_holder')
        if kind == 'marketplace':
            misplaced = [key for key in plugin_only + ('repository',) if args[key] not in (None, False)]
            if misplaced:
                parser.error('create --kind marketplace does not accept ' + ', '.join('--' + key.replace('_', '-') for key in misplaced))
            for key in plugin_only + ('repository',):
                del args[key]
            action = 'create_marketplace'
        else:
            if args['owner'] is not None:
                parser.error('create --kind plugin does not accept --owner')
            if args['marketplace'] is None:
                parser.error('create --kind plugin requires --marketplace')
            del args['owner']
            action = 'create_plugin'
    try:
        result = globals()[action](**args)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr); return 1

if __name__ == '__main__':
    sys.exit(main())
