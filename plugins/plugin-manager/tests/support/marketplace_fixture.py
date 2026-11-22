"""Fictional external-plugin marketplace; no network or personal host state."""
import json
from pathlib import Path
import shutil
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())

def attach(plugin):
    market = plugin.parent/(plugin.name+'-market')
    market.mkdir(exist_ok=True)
    for part in ('sync', 'seed'):  # the files kept in sync and the files created once
        shutil.copytree(ROOT/'skills/_shared/templates/marketplace'/part, market, dirs_exist_ok=True)
    manifest = json.loads((plugin/'plugin.json').read_text())
    name = manifest['name']
    repository = manifest.setdefault('repository', 'https://github.com/example/'+name)
    (plugin/'plugin.json').write_text(json.dumps(manifest))
    config = {'name':'fictional-market', 'displayName':'Fictional Market', 'owner':{'name':'Fictional Team'},
              'plugins':[{'name':name,'displayName':name,'description':manifest['description'],'repository':repository+'.git'}]}
    (market/'marketplace.json').write_text(json.dumps(config))
    (market/'.local').mkdir(exist_ok=True)
    (market/'.local/marketplace.json').write_text(json.dumps({'sources':{name:str(plugin)}}))
    (plugin/'.local').mkdir(exist_ok=True)
    (plugin/'.local/marketplace.json').write_text(json.dumps({'marketplace':str(market)}))
    return market
