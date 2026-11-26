#!/usr/bin/env python3
"""Structure check: manifests, catalogs, skill entry points and the local development mapping. Read-only.
Usage: python3 -B scripts/verify/structure.py --source <repository>. Managed by the plugin manager: do not edit."""
import argparse
import json
from pathlib import Path
import re
import sys
from common import NAME, kind_of, read, safe, skeleton_marker


def plugin(root):
    manifest = read(root, 'plugin.json')
    name = manifest.get('name')
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError('Invalid plugin name')
    if 'version' in manifest:
        raise ValueError('Repository plugin manifests must not pin a version')
    if not isinstance(manifest.get('description'), str) or not manifest['description'].strip():
        raise ValueError('Plugin description is missing')
    distribution = manifest.get('extensions', {}).get('io.zyris.distribution', {})
    if (not isinstance(distribution, dict) or set(distribution) - {'skillRoot', 'files', 'catalogs'}
            or not isinstance(distribution.get('catalogs', False), bool)):
        raise ValueError('Unsupported distribution configuration')
    if distribution.get('skillRoot', 'skills') != 'skills' or distribution.get('catalogs', False):
        raise ValueError('Plugin requires skills/ and no own catalogs')
    for relative in ('.claude/skills', '.agents/skills'):
        if (root/relative).exists() or (root/relative).is_symlink():
            raise ValueError('Host-local source is not canonical: ' + relative)
    extra = distribution.get('files', {})
    if not isinstance(extra, dict):
        raise ValueError('Distribution files must map destination paths to source paths')
    for destination, origin in extra.items():
        if (not isinstance(destination, str) or not destination or Path(destination).is_absolute()
                or any(part in ('.', '..') or part.startswith('.') for part in destination.split('/'))
                or destination == 'plugin.json'):
            raise ValueError('Unsafe or reserved distribution destination')
        if isinstance(origin, str) and (any(part.startswith('.env') for part in Path(origin).parts) or Path(origin).suffix in ('.pem', '.key')):
            raise ValueError('Private distribution source forbidden')
        for mapped in (destination, origin):
            if isinstance(mapped, str) and (set(Path(mapped).parts) & {'.git', '.local', '.tmp', 'dist', '.idea', '.venv', 'node_modules', '__pycache__', '.DS_Store'} or Path(mapped).suffix in ('.pyc', '.pyo', '.pyd')):
                raise ValueError('Generated/local files cannot be distributed: ' + mapped)
        if not safe(root, origin).is_file():
            raise ValueError('Distribution source file missing: ' + str(origin))
    repository = manifest.get('repository', '')
    if not isinstance(repository, str) or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?', repository):
        raise ValueError('Plugin GitHub repository URL is missing or invalid')
    skills = safe(root, 'skills')
    entries = list(skills.glob('*/SKILL.md'))
    if not entries:
        raise ValueError('No skill entry points found under skills/')
    skeleton = False
    for entry in entries:
        entry = safe(root, str(entry.relative_to(root)))
        text = entry.read_text()
        skeleton = skeleton or skeleton_marker(text) is not None
        front = text.split('---', 2)
        if not text.startswith('---\n') or len(front) < 3 or not all(re.search('^' + field + r':\s*\S', front[1], re.M) for field in ('name', 'description')):
            raise ValueError('Missing skill frontmatter: ' + str(entry.relative_to(root)))
    host = manifest.get('extensions', {}).get('com.openai', {})
    interface = host.get('interface', {})
    for relative in [host.get('onboardingSkill'), interface.get('logo'), interface.get('composerIcon')]:
        if relative and not safe(root, relative).is_file():
            raise ValueError('Missing declared plugin asset or entry point: ' + relative)
    claude = read(root, '.claude-plugin/plugin.json')
    expected = {key: manifest[key] for key in ('name','description','author','homepage','repository','license','keywords') if key in manifest}
    expected_claude = dict(expected)
    if interface.get('displayName'):
        expected_claude['displayName'] = interface['displayName']
    if claude != expected_claude:
        raise ValueError('Claude manifest drift')
    codex_path = safe(root, '.codex-plugin/plugin.json')
    if codex_path.exists():
        if read(root, '.codex-plugin/plugin.json') != dict(expected,interface=interface,skills='./skills/'):
            raise ValueError('Codex manifest drift')
    for relative in ('marketplace.json', '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', '.codex-plugin/marketplace.json'):
        if (root/relative).exists() or (root/relative).is_symlink():
            raise ValueError('Plugin repository must not own marketplace catalogs: ' + relative)
    return {'name': name, 'skills': len(entries), 'valid': True,
            'implementation_status': 'skeleton' if skeleton else 'not_assessed'}


def marketplace(root):
    config = read(root, 'marketplace.json')
    if 'version' in config:
        raise ValueError('Marketplace manifests must not pin a version')
    name = config.get('name')
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError('Invalid marketplace name')
    claude = read(root, '.claude-plugin/marketplace.json')
    codex = read(root, '.agents/plugins/marketplace.json')
    for host in (claude, codex):
        if host.get('name') != name:
            raise ValueError('Marketplace identity drift')
    if claude.get('owner') != config.get('owner') or codex.get('interface', {}).get('displayName') != config.get('displayName'):
        raise ValueError('Marketplace owner/displayName drift')
    if not isinstance(config.get('displayName'), str) or not config['displayName'].strip() or not isinstance(config.get('owner'), dict) or not config['owner'].get('name'):
        raise ValueError('Marketplace displayName and owner.name are required')
    if claude.get('metadata', {}).get('description') != config['displayName']:
        raise ValueError('Claude marketplace display metadata drift')
    if not all(isinstance(value.get('plugins'), list) for value in (config, claude, codex)):
        raise ValueError('Marketplace plugins must be lists')
    plugins = []
    expected_claude = {'name':name,'owner':config['owner'],'metadata':{'description':config['displayName']},'plugins':[]}
    expected_codex = {'name':name,'interface':{'displayName':config['displayName']},'plugins':[]}
    for entry in config['plugins']:
        if 'version' in entry:
            raise ValueError('Marketplace entries must not pin a version')
        if 'path' in entry:
            raise ValueError('A marketplace embeds no plugin: each entry names the repository of a separate plugin')
        allowed = {'name', 'displayName', 'description', 'repository'}
        if set(entry) - allowed:
            raise ValueError('Unsupported marketplace entry fields: ' + ', '.join(sorted(set(entry) - allowed)))
        if 'repository' not in entry:
            raise ValueError('Each plugin needs its remote repository')
        repository = entry['repository']
        if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git', repository):
            raise ValueError('Invalid remote GitHub source')
        result = {'name':entry['name'], 'valid':True, 'remote_content_verified':False}
        display, description = entry['displayName'], entry['description']
        sources = ({'source':'url', 'url':repository},) * 2
        if not isinstance(display, str) or not display.strip() or not isinstance(description, str) or not description.strip():
            raise ValueError('Plugin catalog displayName and description must be nonempty strings')
        plugin_name = result['name']
        if not isinstance(plugin_name, str) or not NAME.fullmatch(plugin_name) or any(p['name'] == plugin_name for p in plugins):
            raise ValueError('Duplicate or invalid plugin name')
        for host, source in zip((claude, codex), sources):
            matches = [item for item in host['plugins'] if item.get('name') == plugin_name]
            if len(matches) != 1 or matches[0].get('source') != source or 'version' in matches[0]:
                raise ValueError('Catalog entry/source drift: ' + plugin_name)
        codex_entry = next(item for item in codex['plugins'] if item['name'] == plugin_name)
        if codex_entry.get('policy') != {'installation':'AVAILABLE', 'authentication':'ON_INSTALL'} or codex_entry.get('category') != 'Productivity':
            raise ValueError('Codex catalog policy/category drift: ' + plugin_name)
        matching = next(item for item in claude['plugins'] if item['name'] == plugin_name)
        if matching.get('displayName') != display or matching.get('description') != description:
            raise ValueError('Catalog display metadata drift: ' + plugin_name)
        expected_claude['plugins'].append({'name':plugin_name,'source':sources[0],'description':description,'displayName':display})
        expected_codex['plugins'].append({'name':plugin_name,'source':sources[1],'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Productivity'})
        plugins.append(result)
    if any(len(host['plugins']) != len(plugins) for host in (claude, codex)):
        raise ValueError('Unexpected catalog entries')
    if claude != expected_claude or codex != expected_codex:
        raise ValueError('Marketplace host catalog drift')
    return {'name':name, 'plugins':plugins, 'valid':True}


def local_configuration(root, kind):
    """Optional checkout availability is independent of published structure validity."""
    findings = []
    try:
        # A plugin keeps the path of its one marketplace in the ignored .project/plugins/plugin-manager/local.json,
        # a marketplace the checkouts of its plugins in .local/marketplace.json.
        local_file = '.project/plugins/plugin-manager/local.json' if kind == 'plugin' else '.local/marketplace.json'
        local_path = safe(root, local_file)
        if not local_path.is_file():
            return {'status': 'unavailable', 'complete': False, 'findings': ['No local marketplace configuration (expected on a fresh clone)']}
        local = read(root, local_file)
        if kind == 'plugin':
            if set(local) != {'schema_version', 'marketplace_path'} or local['schema_version'] != 1:
                raise ValueError('Unsupported local marketplace association; run plugin-manager (associate)')
            selected = local['marketplace_path']
            if not isinstance(selected, str) or not selected:
                raise ValueError('No local marketplace path')
            market = Path(selected).expanduser()
            market = market if market.is_absolute() else root/market
            market = market.resolve()
            if not (market/'marketplace.json').is_file():
                raise ValueError('Selected local marketplace checkout unavailable')
            marketplace(market)
            config = read(market, 'marketplace.json')
            manifest = read(root, 'plugin.json')
            repository = manifest['repository'].removesuffix('.git')
            display = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName')
            for entry in config['plugins']:
                if 'path' in entry or entry.get('repository', '').removesuffix('.git') != repository:
                    continue
                if entry.get('name') != manifest['name'] or (display and entry.get('displayName') != display):
                    raise ValueError(
                        f"Marketplace catalog entry '{entry.get('name')}' ('{entry.get('displayName')}') does not match plugin.json "
                        f"'{manifest['name']}' ('{display}'). A plugin repository does not own the catalog: update the entry "
                        "(name, displayName, description) in the marketplace repository and run its make sync.")
            sources = read(market, '.local/marketplace.json').get('sources', {})
            selected_path = sources.get(manifest['name'])
            if not selected_path:
                raise ValueError('Local marketplace does not map this plugin')
            checkout = Path(selected_path).expanduser()
            checkout = checkout if checkout.is_absolute() else market/checkout
            if checkout.resolve() != root:
                raise ValueError('Local marketplace maps a different checkout')
            if not any(e.get('name') == manifest['name'] and e.get('repository', '').removesuffix('.git') == manifest['repository'].removesuffix('.git') for e in config['plugins']):
                raise ValueError('Plugin repository is not registered in the selected marketplace')
        else:
            config = read(root, 'marketplace.json')
            sources = local.get('sources', {})
            if not isinstance(sources, dict):
                raise ValueError('sources must be an object')
            for entry in config['plugins']:
                if 'path' in entry:
                    continue
                selected = sources.get(entry['name'])
                if not isinstance(selected, str) or not selected:
                    findings.append(entry['name'] + ': local checkout unavailable')
                    continue
                checkout = Path(selected).expanduser()
                checkout = checkout if checkout.is_absolute() else root/checkout
                checkout = checkout.resolve()
                try:
                    result = plugin(checkout)
                    manifest = read(checkout, 'plugin.json')
                    if result['name'] != entry['name'] or manifest['repository'].removesuffix('.git') != entry['repository'].removesuffix('.git'):
                        raise ValueError('checkout identity differs from catalog')
                except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
                    findings.append(entry['name'] + ': ' + str(exc))
        return {'status': 'unavailable' if findings else 'complete', 'complete': not findings, 'findings': findings}
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        return {'status': 'unavailable', 'complete': False, 'findings': [str(exc)]}


def verify(source, kind='auto', also=()):
    """The structure of the repository; `also` are further checks `(root, kind)` whose findings fail the same result."""
    root = Path(source).expanduser().resolve()
    selected = kind
    try:
        selected = kind_of(root, kind)
        result = plugin(root) if selected == 'plugin' else marketplace(root)
        for check in also:
            check(root, selected)
        return dict(result, kind=selected, source=str(root), structure_valid=True,
                    local_development=local_configuration(root, selected), target_code_executed=False,
                    limitations=['Structural verification only; host acceptance and remote repository contents require separate checks.'])
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return {'valid': False, 'structure_valid': False, 'kind': selected, 'source': str(root), 'errors': [str(exc)], 'target_code_executed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root')
    parser.add_argument('--kind', choices=['auto', 'plugin', 'marketplace'], default='auto')
    args = parser.parse_args(argv)
    result = verify(args.source, args.kind)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
