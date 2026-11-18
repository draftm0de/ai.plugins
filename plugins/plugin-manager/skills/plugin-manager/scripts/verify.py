#!/usr/bin/env python3
"""Read-only repository verification. Never execute repository code or change files."""
import argparse
import json
from pathlib import Path
import re
import sys
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')

def safe(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Expected a repository-relative path')
    path = root
    for part in Path(relative).parts:
        path /= part
        if path.is_symlink():
            raise ValueError('Symlink is not a verified source: ' + relative)
    return path

def read(root, relative):
    data = json.loads(safe(root, relative).read_text())
    if not isinstance(data, dict):
        raise ValueError(relative + ' must contain a JSON object')
    return data

def plugin(root):
    manifest = read(root, 'plugin.json')
    name = manifest.get('name')
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ValueError('Invalid plugin name')
    if 'version' in manifest:
        raise ValueError('Repository plugin manifests must not pin a version')
    if not manifest.get('description'):
        raise ValueError('Plugin description is missing')
    skills = safe(root, 'skills')
    entries = list(skills.glob('*/SKILL.md'))
    if not entries:
        raise ValueError('No skill entry points found under skills/')
    for entry in entries:
        entry = safe(root, str(entry.relative_to(root)))
        text = entry.read_text()
        front = text.split('---', 2)
        if not text.startswith('---\n') or len(front) < 3 or not all(re.search('^' + field + r':\s*\S', front[1], re.M) for field in ('name', 'description')):
            raise ValueError('Missing skill frontmatter: ' + str(entry.relative_to(root)))
    host = manifest.get('extensions', {}).get('com.openai', {})
    interface = host.get('interface', {})
    for relative in [host.get('onboardingSkill'), interface.get('logo'), interface.get('composerIcon')]:
        if relative and not safe(root, relative).is_file():
            raise ValueError('Missing declared plugin asset or entry point: ' + relative)
    claude = read(root, '.claude-plugin/plugin.json')
    for key in ('name', 'description', 'author', 'repository'):
        if claude.get(key) != manifest.get(key):
            raise ValueError('Claude manifest drift: ' + key)
    if 'version' in claude:
        raise ValueError('Claude manifest must not pin a version')
    if interface.get('displayName') and claude.get('displayName') != interface['displayName']:
        raise ValueError('Claude displayName differs from the portable manifest')
    codex_path = safe(root, '.codex-plugin/plugin.json')
    if codex_path.exists():
        codex = read(root, '.codex-plugin/plugin.json')
        if any(codex.get(key) != manifest.get(key) for key in ('name', 'description', 'repository')) or 'version' in codex:
            raise ValueError('Codex manifest identity/version drift')
        if codex.get('interface', {}) != interface or codex.get('skills') != './skills/':
            raise ValueError('Codex interface or skill-path drift')
    for relative in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
        if (root/relative).exists():
            raise ValueError('Plugin repository must not own marketplace catalogs: ' + relative)
    return {'name': name, 'skills': len(entries), 'valid': True}

def marketplace(root):
    config = read(root, 'marketplace.json')
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
    plugins = []
    for entry in config['plugins']:
        if ('path' in entry) == ('repository' in entry):
            raise ValueError('Each plugin needs exactly one local path or remote repository')
        if 'path' in entry:
            path = entry['path']
            if not path.startswith('./plugins/'):
                raise ValueError('Local plugins must be under ./plugins/')
            directory = safe(root, path)
            result = plugin(directory)
            manifest = read(directory, 'plugin.json')
            display = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {}).get('displayName', result['name'])
            description = manifest['description']
            sources = (path, {'source':'local', 'path':path})
        else:
            repository = entry['repository']
            if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git', repository):
                raise ValueError('Invalid remote GitHub source')
            result = {'name':entry['name'], 'valid':True, 'remote_content_verified':False}
            display, description = entry['displayName'], entry['description']
            sources = ({'source':'url', 'url':repository},) * 2
        plugin_name = result['name']
        if not NAME.fullmatch(plugin_name) or any(p['name'] == plugin_name for p in plugins):
            raise ValueError('Duplicate or invalid plugin name')
        for host, source in zip((claude, codex), sources):
            matches = [item for item in host['plugins'] if item.get('name') == plugin_name]
            if len(matches) != 1 or matches[0].get('source') != source or 'version' in matches[0]:
                raise ValueError('Catalog entry/source drift: ' + plugin_name)
        matching = next(item for item in claude['plugins'] if item['name'] == plugin_name)
        if matching.get('displayName') != display or matching.get('description') != description:
            raise ValueError('Catalog display metadata drift: ' + plugin_name)
        plugins.append(result)
    if any(len(host['plugins']) != len(plugins) for host in (claude, codex)):
        raise ValueError('Unexpected catalog entries')
    return {'name':name, 'plugins':plugins, 'valid':True}

def verify(source, kind='auto'):
    root = Path(source).expanduser().resolve()
    selected = kind
    try:
        if not root.is_dir():
            raise ValueError('Repository directory does not exist')
        has_plugin = (root/'plugin.json').is_file()
        has_marketplace = (root/'marketplace.json').is_file()
        if kind == 'auto':
            if has_plugin == has_marketplace:
                raise ValueError('Cannot infer repository type; select plugin-verify or marketplace-verify and the exact repository root')
            selected = 'plugin' if has_plugin else 'marketplace'
        if selected == 'plugin' and not has_plugin:
            raise ValueError('plugin-verify requires a plugin repository root containing plugin.json')
        if selected == 'marketplace' and not has_marketplace:
            raise ValueError('marketplace-verify requires a marketplace repository root containing marketplace.json')
        result = plugin(root) if selected == 'plugin' else marketplace(root)
        return dict(result, kind=selected, source=str(root), target_code_executed=False,
                    limitations=['Structural verification only; host acceptance and remote repository contents require separate checks.'])
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        return {'valid':False, 'kind':selected, 'source':str(root), 'errors':[str(exc)], 'target_code_executed':False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root, never the installed manager directory by default')
    parser.add_argument('--kind', choices=['auto', 'plugin', 'marketplace'], default='auto')
    args = parser.parse_args()
    result = verify(args.source, args.kind)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['valid'] else 1)
