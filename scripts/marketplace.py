#!/usr/bin/env python3
"""Generate or validate host catalogs from marketplace.json and local plugin manifests."""
import argparse
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def expected(root=ROOT):
    config = json.loads((root/'marketplace.json').read_text())
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', config['name']):
        raise ValueError('Marketplace name must be lowercase kebab-case')
    claude = {'name':config['name'], 'owner':config['owner'], 'metadata':{'description':config['displayName']}, 'plugins':[]}
    codex = {'name':config['name'], 'interface':{'displayName':config['displayName']}, 'plugins':[]}
    seen = set()
    for entry in config['plugins']:
        relative = entry['path']
        if not relative.startswith('./plugins/') or '..' in Path(relative).parts:
            raise ValueError('Plugin path must be under ./plugins/')
        path = root/relative
        if any(part.is_symlink() for part in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Plugin path must not escape the repository or use symlinks')
        manifest = json.loads((path/'plugin.json').read_text())
        name = manifest['name']
        if name in seen or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            raise ValueError('Duplicate or invalid plugin name')
        seen.add(name)
        claude['plugins'].append({'name':name,'source':relative,'description':manifest['description']})
        codex['plugins'].append({'name':name,'source':{'source':'local','path':relative},'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Productivity'})
    return {'.claude-plugin/marketplace.json':claude,'.agents/plugins/marketplace.json':codex}

def sync(check=False):
    drift=[]
    files=expected()
    for relative, data in files.items():
        path=ROOT/relative
        if any(part.is_symlink() for part in (path,*path.parents)):
            raise ValueError('Catalog path must not use symlinks')
        if not path.is_file() or json.loads(path.read_text()) != data:
            drift.append(relative)
    if check and drift:
        raise ValueError('Stale marketplace metadata: '+', '.join(drift))
    if not check:
        for relative in drift:
            path=ROOT/relative;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(files[relative],ensure_ascii=False,indent=0 if relative.startswith('.claude') else 2)+'\n')
    return {'valid':True,'updated':drift}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['check','sync'])
    args=parser.parse_args()
    print(json.dumps(sync(args.action=='check'),indent=2))
