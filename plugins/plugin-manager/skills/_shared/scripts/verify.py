#!/usr/bin/env python3
"""Read-only repository verification. Never execute repository code or change files."""
import argparse
import json
from pathlib import Path
import re
import sys
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')

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
    data = strict_json(safe(root, relative).read_text())
    if not isinstance(data, dict):
        raise ValueError(relative + ' must contain a JSON object')
    return data

def skeleton_marker(text, python=False):
    marker = '<!-- plugin-skeleton: unimplemented -->'
    if python:
        import io, tokenize
        try:
            return next((t.start[0] for t in tokenize.generate_tokens(io.StringIO(text).readline)
                         if t.type == tokenize.COMMENT and t.string.lstrip('#').strip() == marker), None)
        except (tokenize.TokenError, IndentationError):
            return None
    fence = None
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        match = re.match(r'^(`{3,}|~{3,})', stripped)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not stripped[len(token):].strip():
                fence = None
            continue
        if fence is None and line == line.lstrip() and stripped == marker:
            return line_number
    return None

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
        allowed = {'path'} if 'path' in entry else {'name', 'displayName', 'description', 'repository'}
        if set(entry) - allowed:
            raise ValueError('Unsupported marketplace entry fields: ' + ', '.join(sorted(set(entry) - allowed)))
        if ('path' in entry) == ('repository' in entry):
            raise ValueError('Each plugin needs exactly one local path or remote repository')
        if 'path' in entry:
            path = entry['path']
            if name != 'draftmode-ai-plugins' or path != './plugins/plugin-manager':
                raise ValueError('New plugins require separate repositories; only draftmode-ai-plugins/plugins/plugin-manager is embedded')
            directory = safe(root, path)
            result = plugin(directory)
            if result['name'] != 'plugin-manager':
                raise ValueError('Embedded exception is only plugin-manager')
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
        local_path = safe(root, '.local/marketplace.json')
        if not local_path.is_file():
            return {'status': 'unavailable', 'complete': False, 'findings': ['No local marketplace configuration (expected on a fresh clone)']}
        local = read(root, '.local/marketplace.json')
        if kind == 'plugin':
            selected = local.get('marketplace')
            if not isinstance(selected, str) or not selected:
                raise ValueError('No default local marketplace')
            market = Path(selected).expanduser()
            market = market if market.is_absolute() else root/market
            market = market.resolve()
            if not (market/'marketplace.json').is_file():
                raise ValueError('Selected local marketplace checkout unavailable')
            marketplace(market)
            config = read(market, 'marketplace.json')
            manifest = read(root, 'plugin.json')
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
        return dict(result, kind=selected, source=str(root), structure_valid=True,
                    local_development=local_configuration(root, selected), target_code_executed=False,
                    limitations=['Structural verification only; host acceptance and remote repository contents require separate checks.'])
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return {'valid':False, 'structure_valid':False, 'kind':selected, 'source':str(root), 'errors':[str(exc)], 'target_code_executed':False}

def scope_review(root):
    """Collect bounded, explicit evidence. Never claim semantic compliance or run code."""
    import hashlib
    root = Path(root).expanduser().resolve()
    findings = []
    requirements = []
    evidence = []

    def finding(code, file, line, observed, reason, recommendation, requirement=None):
        findings.append(dict(code=code, requirement=requirement, file=file, line=line,
                             observed=observed, reason=reason, recommendation=recommendation))

    def read_text(relative):
        path = safe(root, relative)
        if path.stat().st_size > 512_000:
            raise ValueError('File exceeds review size limit')
        content = path.read_bytes()
        text = content.decode('utf-8')
        evidence.append({'file': relative, 'sha256': hashlib.sha256(content).hexdigest()})
        return text

    def pointer(relative, field):
        parts = Path(relative).parts
        allowed = ('skills', 'scripts', 'tests') if field == 'Source' else ('tests',)
        if (not parts or parts[0] not in allowed or any(p.startswith('.') or p in
                ('fixtures', 'candidate', 'jobs', 'runs', 'node_modules', '__pycache__') for p in parts)
                or Path(relative).suffix not in ('.py', '.md', '.sh', '.js', '.ts')
                or Path(relative).name in ('state.md', 'profile.md')):
            raise ValueError('Outside the allowed public code/test evidence paths')
        return read_text(relative)

    try:
        scope = read_text('SCOPE.md')
    except (OSError, ValueError, UnicodeError) as exc:
        finding('scope_unavailable', 'SCOPE.md', 1, str(exc), 'No readable agreed target is available.',
                'Provide SCOPE.md with confirmed requirements; do not infer requirements from code.')
        scope = ''
    headings = list(re.finditer(r'^## (R[1-9][0-9]*):[ \t]*(.+)$', scope, re.M))
    seen = set()
    if headings:
        preamble = scope[:headings[0].start()]
        if re.findall(r'^Status:[ \t]*(\S[^\n]*)$', preamble, re.M) != ['confirmed']:
            finding('scope_unconfirmed', 'SCOPE.md', 1, 'Scope status is not uniquely confirmed.',
                    'The overall target still requires agreement.', 'Confirm the scope with the user; never promote it automatically.')
    for match in headings:
        next_heading = re.search(r'^## ', scope[match.end():], re.M)
        end = match.end() + next_heading.start() if next_heading else len(scope)
        body = scope[match.end():end]
        identifier, title = match.groups()
        line = scope[:match.start()].count('\n') + 1
        item = dict(id=identifier, title=title.strip(), line=line, semantic_status='unverified',
                    test_execution='not_run', sources=[], tests=[])
        requirements.append(item)
        def fields(name):
            return re.findall(r'^' + name + r':[ \t]*(\S[^\n]*)$', body, re.M)
        if identifier in seen:
            finding('duplicate_requirement', 'SCOPE.md', line, identifier, 'Requirement IDs must be unique.',
                    'Resolve the duplicate without discarding agreed requirements.', identifier)
        seen.add(identifier)
        statuses = fields('Status')
        if statuses != ['confirmed']:
            finding('requirement_unconfirmed', 'SCOPE.md', line, 'Status is not uniquely confirmed.',
                    'Draft requirements cannot establish compliance.', 'Ask the user to confirm or clarify this requirement.', identifier)
        acceptance = fields('Acceptance')
        if len(acceptance) != 1:
            finding('acceptance_missing', 'SCOPE.md', line, 'One acceptance criterion is required.',
                    'A title alone is not a testable target.', 'Record a confirmed observable acceptance criterion.', identifier)
        item['acceptance'] = acceptance[0] if len(acceptance) == 1 else None
        for field, key in (('Source', 'sources'), ('Test', 'tests')):
            refs = fields(field)
            if not refs:
                finding('missing_' + key, 'SCOPE.md', line, 'No ' + field + ' evidence pointer.',
                        'No evidence has been supplied; this does not prove the feature is absent.',
                        'Locate relevant public ' + field.lower() + ' files or report the gap.', identifier)
            for ref in refs:
                try:
                    content = pointer(ref, field)
                    item[key].append(ref)
                    if field == 'Source' and ref.startswith('skills/') and ref.endswith('.py'):
                        import ast
                        try:
                            tree = ast.parse(content)
                            imports = [(n.module, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module and n.level == 0]
                            imports += [(a.name, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
                            for module, import_line in imports:
                                if module.startswith('scripts.'):
                                    development_file = module.replace('.', '/') + '.py'
                                    if safe(root, development_file).is_file():
                                        finding('runtime_imports_development_tool', ref, import_line, 'Import ' + module + ' resolves to root development tooling.',
                                                'Root scripts are not bundled plugin runtime.', 'Move the required runtime module into the distributed skill and update imports/tests.', identifier)
                        except SyntaxError as exc:
                            finding('source_syntax_error', ref, exc.lineno or 1, 'Python syntax cannot be parsed.',
                                    'The supplied source is not syntactically valid Python.', 'Correct the syntax and rerun the review.', identifier)
                    marker = skeleton_marker(content, python=ref.endswith('.py'))
                    if field == 'Source' and marker is not None:
                        finding('skeleton_unimplemented', ref, marker, 'Explicit unimplemented skeleton marker.',
                                'This source disclaims functional behavior.', 'Implement the confirmed requirement and add acceptance tests before removing the marker.', identifier)
                except (OSError, ValueError, UnicodeError) as exc:
                    finding('evidence_unavailable', 'SCOPE.md', line, field + ': ' + ref + ': ' + str(exc),
                            'The evidence cannot safely be inspected.', 'Use an existing public repository-relative source/test file; never follow private paths or symlinks.', identifier)
    if not headings:
        finding('requirements_missing', 'SCOPE.md', 1, 'No R-numbered requirements.',
                'There is no explicit target for a source comparison.', 'Confirm requirements and acceptance criteria before implementing domain behavior.')
    try:
        legacy_tests = safe(root, 'tests/regression').exists()
    except ValueError:
        legacy_tests = False
        finding('unsafe_test_layout', 'tests/regression', 1, 'Symlink test directory was not followed.',
                'Review must stay inside public repository files.', 'Review and resolve the symlink explicitly.')
    if legacy_tests:
        finding('legacy_test_layout', 'tests/regression', 1, 'Separate regression directory.',
                'Regressions belong to their test type.', 'Classify these tests under unit, integration, contracts, behavior or native; preserve every test.')
    for relative in ('AGENTS.md', 'docs/architecture.md'):
        try:
            read_text(relative)
        except (OSError, ValueError, UnicodeError) as exc:
            finding('development_rules_unavailable', relative, 1, str(exc), 'Development rules are not available.',
                    'Add reviewed repository development rules; preserve existing instructions.')
    return {'status': 'needs_attention' if findings else 'ready_for_source_review',
            'semantic_status': 'unverified', 'target_code_executed': False, 'test_execution': 'not_run',
            'requirements': requirements, 'findings': findings, 'evidence': evidence,
            'limitations': ['Evidence pointers and hashes do not prove requirement fulfillment or passing tests.',
                           'The verify skill must separately compare confirmed criteria with source and test logic and cite actual lines.',
                           'Only explicit public evidence files are inspected; private data, host acceptance and remote contents are excluded.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root, never the installed manager directory by default')
    parser.add_argument('--kind', choices=['auto', 'plugin', 'marketplace'], default='auto')
    parser.add_argument('--review', action='store_true', help='Read SCOPE.md and explicit public evidence; semantic review and tests are not automated')
    args = parser.parse_args()
    result = verify(args.source, args.kind)
    if args.review:
        result['review'] = scope_review(args.source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['valid'] and (not args.review or result['review']['status'] == 'ready_for_source_review') else 1)
