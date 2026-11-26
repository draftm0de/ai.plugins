#!/usr/bin/env python3
"""Scope review (REVIEW=1): collects the evidence SCOPE.md names; never claims that a requirement is met. Read-only.
Usage: python3 -B scripts/verify/scope.py --source <repository>. Managed by the plugin manager: do not edit."""
import argparse
import json
from pathlib import Path
import re
import sys
from common import safe, skeleton_marker


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
        name = Path(relative).name
        suffix = Path(relative).suffix
        # Published templates and hash files of a skill are source too, with their own file types.
        delivered = field == 'Source' and len(parts) > 3 and parts[0] == 'skills' and parts[2] in ('templates', 'manifests')
        readable = suffix in ('.py', '.md', '.sh', '.js', '.ts') or delivered and (
            suffix in ('.json', '.yml') or name in ('Makefile', 'pre-commit'))
        hidden = [p for p in parts if p.startswith('.') and not (delivered and p == '.github' and suffix == '.yml')]
        if (not parts or parts[0] not in allowed or hidden or any(p in
                ('fixtures', 'candidate', 'jobs', 'runs', 'node_modules', '__pycache__') for p in parts)
                or not readable or name in ('state.md', 'profile.md')):
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.cwd(), help='Project repository root')
    result = scope_review(parser.parse_args(argv).source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'ready_for_source_review' else 1


if __name__ == '__main__':
    sys.exit(main())
