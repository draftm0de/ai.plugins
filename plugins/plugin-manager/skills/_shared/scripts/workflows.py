#!/usr/bin/env python3
"""Create separate repositories and configure associations. Never commit or publish."""
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
    if not isinstance(value, str):
        raise ValueError('GitHub repository URL required')
    value = value.removesuffix('.git')
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', value)
    if not match:
        raise ValueError('Use a credential-free GitHub repository URL')
    return 'https://github.com/' + match[1]


def git_repository(root, supplied=None):
    actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], text=True).strip()
    if Path(actual).resolve() != root.resolve():
        raise ValueError('Select the exact separate repository root')
    origin = repository_url(subprocess.check_output(['git', '-C', str(root), 'config', '--get', 'remote.origin.url'], text=True).strip())
    if supplied and repository_url(supplied) != origin:
        raise ValueError('Explicit repository URL conflicts with Git origin')
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


def ignore_file(root):
    path = safe_path(root/'.gitignore')
    text = path.read_text() if path.exists() else ''
    for pattern in (SKILL/'templates/plugin/gitignore.txt').read_text().splitlines():
        if not pattern or pattern.startswith('#'):
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
        probe = '.local/marketplace.json'
        result = isolated_git(shadow, 'check-ignore', '--no-index', '--', probe)
        if result.returncode not in (0, 1):
            raise ValueError('Cannot evaluate proposed Git ignore rules')
        if probe not in result.stdout.splitlines():
            raise ValueError('Ineffective Git ignore rules for .local/marketplace.json in ' + str(root) +
                             '; review .gitignore and .local/.gitignore before writing associations')
    return path, text.encode()


def catalog_files(root, config):
    engine = module(SKILL/'templates/marketplace/scripts/marketplace.py', 'catalog_template')
    return {root/path: encode(data) for path, data in engine.expected(root, config).items()}


def template_files(kind, root):
    folder = SKILL/'templates'/kind
    return {root/p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def marketplace_create(root, name=None, display_name=None, owner=None, repository=None):
    root = safe_path(root)
    origin = git_repository(root, repository)
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
    config = existing or {'name': name, 'displayName': display_name, 'owner': publisher, 'repository': origin, 'plugins': []}
    files = template_files('marketplace', root)
    files[root/'marketplace.json'] = encode(config)
    files.update(catalog_files(root, config))
    # Keep existing project prose and licensing untouched.
    for lang, filename in (('de', 'README.md'), ('en', 'README.en.md')):
        if not (root/filename).exists():
            text = (f'# {display_name}\n\nMarketplace `{name}`: {origin}\n\n' +
                ('Plugin-Repositories werden in `marketplace.json` eingetragen. Lokale Pfade stehen ausschließlich in `.local/marketplace.json`.\n\n' if lang == 'de' else 'Plugin repositories are registered in `marketplace.json`. Local paths belong only in `.local/marketplace.json`.\n\n') +
                '```sh\nmake verify\nmake check-marketplace\nmake install-local TARGET=claude\nmake update-local TARGET=codex\n```\n\n' +
                ('Ein frischer Clone benötigt für lokale Installation zuerst Checkout-Zuordnungen über configure. local-marketplace.example.json ist nur eine optionale manuelle Kopiervorlage; nur .local/marketplace.json wird zur Laufzeit gelesen und bleibt uncommitted. Snapshots verwenden den aktuellen Checkout einschließlich uncommitteter Änderungen auf jedem Branch. Nach Änderungen oder Branchwechsel update-local und eine neue Host-Sitzung; kein Commit/Push/PR und kein Marketplace pro Branch. [Voraussetzungen](docs/prerequisites.md): Git und Python 3.10+, Make optional, Host-CLI nur für automatische lokale Installation. Strukturprüfung ist keine GitHub-/GUI-Abnahme.\n' if lang == 'de' else 'A fresh clone needs checkout associations through configure before local installation. local-marketplace.example.json is only an optional manual template; only .local/marketplace.json is read at runtime and stays uncommitted. Snapshots use the current checkout including uncommitted edits on any branch. After edits or branch switches run update-local and open a new host session; no commit/push/PR or per-branch marketplace. [Prerequisites](docs/prerequisites.md): Git and Python 3.10+, optional Make, host CLI only for automatic local installation. Structural verification is not GitHub/GUI acceptance.\n'))
            files[root/filename] = text.encode()
    ignore, content = ignore_file(root); files[ignore] = content
    return {'action': 'marketplace-create', 'changed': apply(files, [ignore]), 'repository': origin, 'published': False}


def association_files(plugin_root, market, manifest):
    market = safe_path(market)
    git_repository(market)
    verifier = module(SKILL/'scripts/verify.py', 'trusted_verify')
    verifier.marketplace(market)
    config = read(market/'marketplace.json')
    name = manifest['name']
    url = repository_url(manifest['repository'])
    entry = {'name': name, 'displayName': manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName', name),
             'description': manifest['description'], 'repository': url + '.git'}
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
    for checkout in (market, plugin_root):
        if subprocess.check_output(['git', '-C', str(checkout), 'ls-files', '--', '.local']).strip():
            raise ValueError('Local configuration is tracked; review before writing private checkout mappings')
    local = read(market/'.local/marketplace.json', {})
    sources = local.setdefault('sources', {})
    if name in sources:
        previous = Path(sources[name]).expanduser()
        previous = previous if previous.is_absolute() else market/previous
        if previous.resolve() != plugin_root.resolve():
            raise ValueError('Existing local checkout differs; review this mapping before replacement')
    sources[name] = os.path.relpath(plugin_root, market)
    plugin_local = read(plugin_root/'.local/marketplace.json', {})
    associations = plugin_local.setdefault('marketplaces', {})
    old_default = plugin_local.get('marketplace')
    if old_default:
        old = Path(old_default).expanduser()
        old = old if old.is_absolute() else plugin_root/old
        if (old/'marketplace.json').is_file():
            old_name = read(old/'marketplace.json')['name']
            associations.setdefault(old_name, os.path.relpath(old, plugin_root))
    relative = os.path.relpath(market, plugin_root)
    if config['name'] in associations:
        previous = Path(associations[config['name']]).expanduser()
        previous = previous if previous.is_absolute() else plugin_root/previous
        if previous.resolve() != market.resolve():
            raise ValueError('Marketplace identity already maps to a different checkout')
    associations[config['name']] = relative
    plugin_local['marketplace'] = relative
    files = {market/'marketplace.json': encode(config), market/'.local/marketplace.json': encode(local),
             plugin_root/'.local/marketplace.json': encode(plugin_local)}
    files.update(catalog_files(market, config))
    for root in (market, plugin_root):
        path, content = ignore_file(root); files[path] = content
    return files


def configure(root, marketplace, repository=None):
    root = safe_path(root); market = safe_path(marketplace)
    origin = git_repository(root, repository)
    if root == market or root.is_relative_to(market) or market.is_relative_to(root):
        raise ValueError('Use separate plugin and marketplace repositories')
    verifier = module(SKILL/'scripts/verify.py', 'trusted_verify')
    verifier.plugin(root)
    manifest = read(root/'plugin.json')
    if repository_url(manifest['repository']) != origin:
        raise ValueError('Plugin manifest conflicts with Git origin')
    files = association_files(root, market, manifest)
    replace = list(files)
    template = SKILL/'templates/plugin'
    # Add only missing developer entry points; existing tooling is not silently replaced.
    for relative in ('scripts/plugin.py', 'scripts/verify.py', 'install.sh'):
        path = safe_path(root/relative)
        if not path.exists():
            files[path] = (template/relative).read_bytes()
    if not (root/'Makefile').exists():
        block = (template/'Makefile').read_text().split('# Local development and repository metadata', 1)[1]
        files[root/'Makefile'] = ('export PYTHONDONTWRITEBYTECODE := 1\nPYTHON ?= python3\nTARGET ?= claude\nDRY_RUN ?= 0\nMARKETPLACE ?=\n# Local development and repository metadata' + block).encode()
    else:
        makefile = safe_path(root/'Makefile')
        text = makefile.read_text()
        missing = [action for action in ('install-local', 'update-local')
                   if not re.search(r'^' + action + r'(?:\s+[^:\n]+)?\s*:', text, re.M)
                   and not re.search(r'^[^#\n:]*\b' + action + r'\b[^\n:]*:', text, re.M)]
        if missing:
            engine = root/'scripts/plugin.py'
            if engine.exists() and engine.read_bytes() != (template/'scripts/plugin.py').read_bytes():
                raise ValueError('Existing plugin tooling needs a reviewed Makefile integration before configure')
            text += '\n# Local marketplace commands (Plugin Manager)\nPYTHON ?= python3\nTARGET ?= claude\nDRY_RUN ?= 0\nMARKETPLACE ?=\n'
            for action in missing:
                text += f'.PHONY: {action}\n{action}:\n\t$(PYTHON) scripts/plugin.py {action} --target "$(TARGET)" $(if $(MARKETPLACE),--marketplace "$(MARKETPLACE)",) $(if $(filter 1,$(DRY_RUN)),--dry-run,)\n'
            files[makefile] = text.encode(); replace.append(makefile)
    return {'action': 'configure', 'changed': apply(files, replace), 'published': False}


def complete_skeleton_documentation(stage, title):
    """Fill only newly staged pages; never rewrite existing user documentation."""
    from documentation import language_policy, page_layout, validate
    content = read(SKILL/'templates/skeleton-content.json')
    for relative, (_, _, language) in page_layout(language_policy(stage)).items():
        path = stage/relative
        text = path.read_text()
        page = content[language]
        if relative.startswith('README'):
            text = re.sub(r'^# .*', lambda _: '# ' + title, text, count=1)
            text = text.replace('{{SUMMARY}}', page['summary'])
            sections = page['root']
        else:
            sections = page[path.name]
        for index, paragraph in enumerate(sections, 1):
            text = text.replace('{{CONTENT_' + f'{index:02d}' + '}}', paragraph)
        path.write_text(text)
    errors = validate(stage)
    if errors:
        raise ValueError('Skeleton documentation validation failed: ' + '; '.join(errors))


def creation_checks(root, market):
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
    checks['functional_acceptance'] = 'pending'
    checks['tests'] = 'not_run'
    checks['host_acceptance'] = 'not_run'
    return checks


def plugin_create(root, marketplace, source=None, name=None, display_name=None, description=None, repository=None, author=None, languages=None, default_language=None, skeleton=False, _skeleton_documentation=False):
    if skeleton:
        if source is not None:
            raise ValueError("Choose either --skeleton or --source, not both")
        identity(name, display_name)
        with tempfile.TemporaryDirectory() as directory:
            stub = Path(directory).resolve()/name
            stub.mkdir()
            (stub/"SKILL.md").write_text("---\nname: " + name + "\ndescription: Unimplemented plugin skeleton; no domain behavior is available.\n---\n\n# Plugin skeleton\n\n<!-- plugin-skeleton: unimplemented -->\n\nThis is a nonfunctional development skeleton. Do not perform domain actions or claim capabilities. Read SCOPE.md in the source repository and clarify requirements before implementing. Remove the skeleton marker only after implementing and reviewing the agreed behavior.\n")
            result = plugin_create(root, marketplace, stub, name, display_name, description or "Unimplemented plugin skeleton; domain requirements are pending.", repository, author, languages, default_language, _skeleton_documentation=True)
            result.update(implementation_status="skeleton", next="Confirm SCOPE.md, implement agreed behavior under skills/, add tests, then run verify --review. No functional acceptance is claimed.")
            if result['checks']['status'] != 'passed':
                result['next'] = 'Resolve the reported creation checks before claiming completion. ' + result['next']
            return result
    if source is None:
        raise ValueError("Choose --skeleton for an empty product or --source for an existing skill")
    root = safe_path(root); market = safe_path(marketplace); source = safe_path(source)
    if root == market or root.is_relative_to(market) or market.is_relative_to(root):
        raise ValueError('Use separate plugin and marketplace repositories')
    if root == source or source.is_relative_to(root) or root.is_relative_to(source):
        raise ValueError('Source skill and output must be separate')
    if not root.exists():
        url = repository_url(repository)
        root.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'init.templateDir=', 'clone', '--', url + '.git', str(root)], check=True)
    origin = git_repository(root, repository)
    if (root/'plugin.json').exists() or (root/'marketplace.json').exists():
        raise ValueError('Product already exists; use configure for an existing plugin')
    for obsolete in ('.claude/skills', '.agents/skills', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', '.codex-plugin/marketplace.json'):
        if (root/obsolete).exists() or (root/obsolete).is_symlink():
            raise ValueError('Unsupported host-local skill layout: ' + obsolete)
    from documentation import inspect
    info = inspect(source)
    name = name or info['name']
    identity(name, display_name)
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
        scaffold_plugin(source, stage, languages, default_language, origin, author, name)
        manifest = read(stage/'plugin.json')
        manifest['description'] = description
        manifest['extensions']['com.openai'] = {'interface': {'displayName': display_name}}
        (stage/'plugin.json').write_bytes(encode(manifest))
        engine = module(SKILL/'templates/plugin/scripts/plugin.py', 'trusted_payload')
        for path, data in engine.repository_files(manifest).items():
            (stage/path).write_bytes(encode(data))
        if _skeleton_documentation:
            complete_skeleton_documentation(stage, display_name)
        files = {root/p.relative_to(stage): p.read_bytes() for p in stage.rglob('*') if p.is_file()}
        # Existing prose and licenses remain canonical; docs action can later merge them.
        for path in list(files):
            if (path.exists() and path not in (root/'docs/architecture.md', root/'docs/prerequisites.md')
                    and (path.name.startswith('README') or path.is_relative_to(root/'docs'))):
                del files[path]
        association = association_files(root, market, manifest)
        files.update(association)
        changes = apply(files, association.keys())
    return {'action': 'plugin-create', 'changed': changes, 'repository': origin, 'published': False,
            'checks': creation_checks(root, market),
            'next': 'Complete documentation templates from the actual skill source; verify structure, test behavior and perform separate host acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Requires Git and Python 3.10+; Make is optional. configure is normal setup; the example JSON is only a manual template. No automatic tool installation.')
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('marketplace-create', 'plugin-create', 'configure'):
        command = sub.add_parser(action)
        command.add_argument('--root', type=Path, default=Path.cwd(), help='User project root, never manager installation')
        command.add_argument('--repository')
        if action != 'configure':
            command.add_argument('--name'); command.add_argument('--display-name')
        if action == 'marketplace-create':
            command.add_argument('--owner')
        else:
            command.add_argument('--marketplace', type=Path, required=True)
        if action == 'plugin-create':
            mode = command.add_mutually_exclusive_group(required=True)
            mode.add_argument('--source', type=Path, help='Existing or explicitly authored skill')
            mode.add_argument('--skeleton', action='store_true', help='Nonfunctional skeleton with pending SCOPE.md; no invented domain content')
            command.add_argument('--description'); command.add_argument('--author')
            command.add_argument('--languages', nargs='+', choices=['de','en'])
            command.add_argument('--default-language', choices=['de','en'])
    parsed, unknown = parser.parse_known_args()
    args = vars(parsed); action = args.pop('action')
    if unknown:
        parser.error('unrecognized arguments: ' + ' '.join(unknown))
    try:
        result = globals()[action.replace('-', '_')](**args)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr); return 1

if __name__ == '__main__':
    sys.exit(main())
