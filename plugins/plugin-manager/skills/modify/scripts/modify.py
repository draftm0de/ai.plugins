#!/usr/bin/env python3
"""Change what a plugin or marketplace repository states about itself (R24): name, display name, description.

The kind comes from the configuration evidence of the workpackage, never from the call. All files of one change are
written in one rollback-capable transaction. Nothing is committed, pushed, installed or published, and no
documentation or tests are rewritten. The shared generator library is imported from skills/_shared/scripts."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '_shared/scripts'))
import workflows as flow  # noqa: E402

NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
PUBLISH_NOTE = ('The changed files are committed files left unversioned; publish them through /plugin-manager:publish '
                '(plugin and marketplace repositories separately). Nothing was committed, pushed, installed or published.')
DOCS_NOTE = ('Call forms (/<name>:<skill>, <name>@<marketplace>), documentation and tests that name the old values are not '
             'rewritten here; refresh the documentation with /plugin-manager:docs.')


def check_values(name, display_name, description):
    if name is not None and not NAME.fullmatch(name):
        raise ValueError('The technical name must be lowercase kebab-case')
    if display_name is not None and not display_name.strip():
        raise ValueError('The display name must not be empty')
    if description is not None and not description.strip():
        raise ValueError('The description must not be empty')


def modify(root, *, name=None, display_name=None, description=None, plugin=flow.OWNER, dry_run=False):
    """Change name, display name and/or description of the plugin or marketplace at `root`.
    dry_run writes nothing and lists the files that would change (`would_change`), to show the consequences first."""
    check_values(name, display_name, description)
    if name is None and display_name is None and description is None:
        raise ValueError('Nothing to change: give a name, a display name or a description')
    root = flow.safe_path(root)
    evidence, _ = flow.load_evidence(root, plugin)
    if evidence is None:
        raise ValueError('Configure first: this workpackage has no configuration evidence for ' + plugin + ' (run /plugin-manager:setup)')
    if evidence['kind'] == 'plugin':
        return modify_plugin(root, evidence, name, display_name, description, plugin, dry_run)
    if evidence['kind'] == 'marketplace':
        return modify_marketplace(root, evidence, name, display_name, description, plugin, dry_run)
    raise ValueError('Unsupported kind in the configuration evidence: ' + str(evidence['kind']))


def write(files, dry_run):
    """(changed, pending): the files written now and the files whose bytes differ. A dry run writes nothing."""
    pending = [str(path) for path, content in files.items() if not path.exists() or path.read_bytes() != content]
    return ([], pending) if dry_run else (flow.apply(files, list(files)), pending)


def display_name_of(manifest):
    return manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName', manifest['name'])


def available_marketplace(root, evidence):
    """The marketplace checkout named by the ignored local.json when it is present and carries the configured identity."""
    previous = flow.plugin_local_association(root)
    if not previous:
        return None
    candidate = flow.checkout_path(root, previous)
    if not (candidate / 'marketplace.json').is_file():
        return None
    return candidate if flow.market_identity(candidate)['name'] == evidence['marketplace']['name'] else None


def modify_plugin(root, evidence, name, display_name, description, plugin, dry_run=False):
    verifier = flow.module(flow.SKILL / 'scripts/verify.py', 'trusted_verify')
    verifier.plugin(root)
    manifest = flow.read(root / 'plugin.json')
    if manifest['name'] != evidence['artifact']:
        raise ValueError('plugin.json carries another name than the configuration evidence (' + evidence['artifact'] + ')')
    new = json.loads(json.dumps(manifest))
    if name is not None:
        new['name'] = name
    if display_name is not None:
        new.setdefault('extensions', {}).setdefault('com.openai', {}).setdefault('interface', {})['displayName'] = display_name
    if description is not None:
        new['description'] = description
    values_changed = new != manifest
    engine = flow.module(flow.SKILL / 'templates/plugin/sync/scripts/plugin.py', 'trusted_payload')
    files = {root / 'plugin.json': flow.encode(new)}
    for path, data in engine.repository_files(new).items():
        files[root / path] = flow.encode(data)
    if new['name'] != manifest['name']:
        updated = dict(evidence)
        updated['artifact'] = new['name']
        files[root / flow.EVIDENCE_FILE.format(plugin=plugin)] = flow.encode(updated)
    market = available_marketplace(root, evidence)
    if market is not None:
        files.update(catalog_update(root, market, manifest, new))
    changed, pending = write(files, dry_run)
    notes = [DOCS_NOTE, PUBLISH_NOTE] if pending else []
    remains = market is None and values_changed
    if remains:
        notes.insert(0, 'The marketplace checkout is not available: change the catalog entry of the plugin there (name, displayName, '
                        'description), then regenerate its catalogs.')
    return {'action': 'modify', 'kind': 'plugin', 'dry_run': dry_run, 'changed': changed, 'would_change': pending, 'published': False,
            'from': {'name': manifest['name'], 'displayName': display_name_of(manifest), 'description': manifest['description']},
            'to': {'name': new['name'], 'displayName': display_name_of(new), 'description': new['description']},
            'catalog_entry_remains': remains, 'affected_plugins': [], 'follow_up': notes}


def catalog_update(root, market, old, new):
    """Files that carry the changed identity into the catalog entry of the plugin and the local checkout mapping."""
    verifier = flow.module(flow.SKILL / 'scripts/verify.py', 'trusted_verify')
    verifier.marketplace(market)
    if flow.git_tracked(market, '.local'):
        raise ValueError('Local configuration is tracked; review before writing private checkout mappings')
    url = flow.repository_url(new['repository'])
    config = flow.read(market / 'marketplace.json')
    entries, found = [], False
    for entry in config['plugins']:
        if entry.get('name') == old['name'] and entry.get('repository') and flow.repository_url(entry['repository']) == url:
            entries.append(flow.plugin_entry(new, url))
            found = True
            continue
        if new['name'] != old['name'] and entry.get('name') == new['name']:
            raise ValueError('The name ' + new['name'] + ' is already registered in the marketplace for another plugin')
        entries.append(entry)
    if not found:
        raise ValueError('The marketplace does not list this plugin (name and repository); associate it first (/plugin-manager:setup)')
    config['plugins'] = entries
    local = flow.read(market / '.local/marketplace.json', {})
    sources = local.get('sources', {})
    if old['name'] in sources and flow.checkout_path(market, sources[old['name']]).resolve() != root.resolve():
        raise ValueError('Existing local checkout differs; review this mapping before replacement')
    if new['name'] != old['name']:
        sources.pop(old['name'], None)
        sources[new['name']] = os.path.relpath(root, market)
        local['sources'] = sources
    files = {market / 'marketplace.json': flow.encode(config)}
    files.update(flow.catalog_files(market, config))
    if new['name'] != old['name']:
        files[market / '.local/marketplace.json'] = flow.encode(local)
    return files


def modify_marketplace(root, evidence, name, display_name, description, plugin, dry_run=False):
    if description is not None:
        raise ValueError('A marketplace has no description; change its name or display name')
    verifier = flow.module(flow.SKILL / 'scripts/verify.py', 'trusted_verify')
    verifier.marketplace(root)
    config = flow.read(root / 'marketplace.json')
    if config['name'] != evidence['artifact']:
        raise ValueError('marketplace.json carries another name than the configuration evidence (' + evidence['artifact'] + ')')
    new = dict(config)
    if name is not None:
        new['name'] = name
    if display_name is not None:
        new['displayName'] = display_name
    files = {root / 'marketplace.json': flow.encode(new)}
    files.update(flow.catalog_files(root, new))
    if new['name'] != config['name']:
        updated = dict(evidence)
        updated['artifact'] = new['name']
        files[root / flow.EVIDENCE_FILE.format(plugin=plugin)] = flow.encode(updated)
    sources = flow.read(root / '.local/marketplace.json', {}).get('sources', {})
    affected = [{'name': key, 'path': value} for key, value in sorted(sources.items())] if new['name'] != config['name'] else []
    changed, pending = write(files, dry_run)
    notes = []
    if affected:
        notes.append('Plugin repositories keep the old marketplace name in their configuration; in each, run /plugin-manager:setup '
                     '(association) so associate takes the new name. They were not changed.')
    if pending:
        notes += [DOCS_NOTE, PUBLISH_NOTE]
    return {'action': 'modify', 'kind': 'marketplace', 'dry_run': dry_run, 'changed': changed, 'would_change': pending, 'published': False,
            'from': {'name': config['name'], 'displayName': config.get('displayName', config['name'])},
            'to': {'name': new['name'], 'displayName': new.get('displayName', new['name'])},
            'catalog_entry_remains': False, 'affected_plugins': affected, 'follow_up': notes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='The plugin or marketplace repository, never the Manager installation')
    parser.add_argument('--name', help='New technical name (lowercase kebab-case)')
    parser.add_argument('--display-name', help='New display name')
    parser.add_argument('--description', help='New description (plugin only)')
    parser.add_argument('--plugin', default=flow.OWNER, help='Running plugin that owns the workpackage evidence')
    parser.add_argument('--dry-run', action='store_true', help='Write nothing; list the files that would change')
    args = parser.parse_args(argv)
    if args.name is None and args.display_name is None and args.description is None:
        parser.error('give at least one of --name, --display-name, --description')
    try:
        print(json.dumps(modify(args.root, name=args.name, display_name=args.display_name, description=args.description,
                                plugin=args.plugin, dry_run=args.dry_run), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
