#!/usr/bin/env python3
"""Opt-in prompt-only model cases for the skills of this plugin. Managed by the plugin manager, identical in every plugin.

A case (tests/fixtures/skills/cases.json, owned by the plugin) holds the real skill texts, the output of the commands the
skill starts with (fictional, already run) and the conversation so far. The model has no tools and answers with what it
would say and run next; the grading is deterministic. One run on one model shows that the text steers a model, not how
often; it does not test host routing."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / 'tests/fixtures/skills/cases.json'
STRING = {'type': 'string'}
SCHEMA = {'type': 'object', 'additionalProperties': False,
          'properties': {'reply': STRING, 'commands': {'type': 'array', 'items': STRING},
                         'next_step': {'type': 'string', 'enum': ['reports_only', 'asks_question', 'asks_confirmation']},
                         'options': {'type': 'array', 'items': STRING}, 'writes': {'type': 'boolean'}},
          'required': ['reply', 'commands', 'next_step', 'options', 'writes']}
ENGLISH = {'the', 'and', 'is', 'not', 'to', 'of', 'this', 'run', 'first', 'please', 'before', 'with', 'was', 'are', 'it', 'you'}
GERMAN = {'der', 'die', 'das', 'und', 'ist', 'nicht', 'zu', 'bitte', 'zuerst', 'vor', 'mit', 'wurde', 'sind', 'es', 'sie', 'noch', 'bevor', 'kann'}


def language_of(text):
    tokens = re.findall(r"[a-zäöüß]+", text.casefold())
    english, german = sum(w in ENGLISH for w in tokens), sum(w in GERMAN for w in tokens)
    return 'de' if german > english else 'en' if english > german else 'unknown'


def build_prompt(case, root=ROOT):
    sources = '\n\n'.join('--- ' + name + ' ---\n' + (root / name).read_text(encoding='utf-8') for name in case['sources'])
    observed = '\n\n'.join('$ ' + o['command'] + '\n' + o['output'] for o in case['observed'])
    history = '\n'.join(item['role'].upper() + ': ' + item['text'] for item in case['history'])
    return ('You are the agent that has just loaded the skill below. All tools are unavailable: you cannot run commands or '
            'write files. Say what you would write to the person and which shell commands you would run next, in order. '
            'The commands the skill starts with have already been run for you; their output is below and is real. '
            'Follow the skill and its shared rules exactly; do not invent results of commands you have not been given. '
            'Return only one JSON object matching the schema: reply (what you write to the person now), commands (shell commands '
            'you would run now, possibly none), next_step (reports_only, asks_question or asks_confirmation: you end by asking for '
            'an explicit yes), options (the answer buttons you offer with a question, in order; empty when none), writes (true only '
            'if your commands change files).\n\nSKILL TEXTS:\n' + sources + '\n\nOUTPUT ALREADY OBSERVED:\n' + observed
            + '\n\nCONVERSATION SO FAR:\n' + history)


def grade(case, report):
    """Deterministic grading of one answer against case['expect']; returns the list of errors."""
    expect, errors = case['expect'], []
    reply, commands = report.get('reply', ''), report.get('commands', [])
    if not isinstance(reply, str) or not reply.strip():
        return ['empty reply']
    if 'language' in expect and language_of(reply) != expect['language']:
        errors.append('reply is not in ' + expect['language'])
    for key in ('mentions', 'contains'):
        for needle in expect.get(key, []):
            if needle.casefold() not in reply.casefold():
                errors.append('reply does not ' + ('mention ' if key == 'mentions' else 'contain ') + needle)
    position = 0
    for part in expect.get('in_order', []):
        found = reply.casefold().find(part.casefold(), position)
        if found < 0:
            errors.append('reply lacks "' + part + '" in the required order')
            break
        position = found + len(part)
    for pattern in expect.get('forbidden_text', []):
        if re.search(pattern, reply, re.IGNORECASE):
            errors.append('reply contains technical wording matching ' + pattern)
    if expect.get('mentions_any') and not any(n.casefold() in reply.casefold() for n in expect['mentions_any']):
        errors.append('reply mentions none of ' + ', '.join(expect['mentions_any']))
    if 'next_step' in expect:
        allowed = expect['next_step'] if isinstance(expect['next_step'], list) else [expect['next_step']]
        if report.get('next_step') not in allowed:
            errors.append('next_step is ' + str(report.get('next_step')) + ', expected ' + ' or '.join(allowed))
    if 'options' in expect and report.get('options') != expect['options']:
        errors.append('options are ' + str(report.get('options')) + ', expected ' + str(expect['options']))
    if 'writes' in expect and report.get('writes') is not expect['writes']:
        errors.append('writes is ' + str(report.get('writes')) + ', expected ' + str(expect['writes']))
    if 'max_questions' in expect and sum('?' in line for line in reply.splitlines()) > expect['max_questions']:
        errors.append('more than ' + str(expect['max_questions']) + ' question(s)')
    for pattern in expect.get('required_commands', []):
        if not any(re.search(pattern, c) for c in commands):
            errors.append('missing command matching ' + pattern)
    for pattern in expect.get('forbidden_commands', []):
        if any(re.search(pattern, c) for c in commands):
            errors.append('forbidden command matching ' + pattern)
    return errors


def parse_report(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    return json.loads(text)


def command(cli, schema_file, response):
    if cli == 'claude':
        return ['claude', '-p', '--safe-mode', '--restricted', '--tools', '', '--strict-mcp-config', '--no-session-persistence',
                '--disable-slash-commands', '--output-format', 'json', '--json-schema', json.dumps(SCHEMA)]
    args = ['codex', 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json',
            '--output-schema', str(schema_file), '--output-last-message', str(response)]
    for feature in ('shell_tool', 'unified_exec', 'apps', 'plugins', 'hooks', 'multi_agent', 'browser_use', 'computer_use'):
        args += ['--disable', feature]
    return args + ['-']


def run_case(cli, case, output, timeout):
    output.mkdir(parents=True, exist_ok=False)
    prompt = build_prompt(case)
    (output / 'prompt.txt').write_text(prompt)
    with tempfile.TemporaryDirectory(prefix='fictional-skill-') as directory:
        work = Path(directory).resolve()
        schema_file, response = work / 'schema.json', work / 'response.json'
        schema_file.write_text(json.dumps(SCHEMA))
        errors, report = [], None
        try:
            proc = subprocess.run(command(cli, schema_file, response), input=prompt, cwd=work, text=True,
                                  capture_output=True, timeout=timeout, check=False)
            code, stdout = proc.returncode, proc.stdout
        except subprocess.TimeoutExpired:
            code, stdout = 124, ''
        (output / 'stdout.jsonl').write_text(stdout)
        if code:
            errors.append('CLI exit code ' + str(code))
        try:
            if cli == 'claude':
                envelope = json.loads(stdout)
                if envelope.get('is_error'):
                    errors.append('Claude reported an error')
                report = envelope.get('structured_output') or parse_report(envelope.get('result', ''))
            else:
                report = parse_report(response.read_text())
            errors += grade(case, report)
        except (ValueError, TypeError, AttributeError, KeyError, OSError) as exc:
            errors.append('Invalid or missing model answer: ' + str(exc))
    result = {'case': case['id'], 'cli': cli, 'errors': errors, 'passed': not errors, 'report': report,
              'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'limitations': ['Prompt-only evaluation of the skill texts; no host routing, no tool use.']}
    (output / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', choices=['claude', 'codex'])
    parser.add_argument('--case')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args(argv)
    if not CASES.is_file():
        print('NOT RUN: no model cases at tests/fixtures/skills/cases.json')
        return 0
    cases = json.loads(CASES.read_text())
    if args.case:
        cases = [c for c in cases if c['id'] == args.case]
    if not cases:
        parser.error('unknown case')
    if args.list:
        print('\n'.join(case['id'] for case in cases))
        return 0
    if not args.cli:
        parser.error('--cli required')
    if not shutil.which(args.cli):
        parser.error('CLI unavailable; no automatic installation')
    output = ROOT / '.tmp/tests/behavior' / args.cli / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for case in cases:
        result = run_case(args.cli, case, output / case['id'], args.timeout)
        results.append(result)
        print(('PASS ' if result['passed'] else 'FAIL ') + case['id'] + ': ' + '; '.join(result['errors']), flush=True)
    (output / 'summary.json').write_text(json.dumps({'results': results}, indent=2, ensure_ascii=False) + '\n')
    print(str(sum(r['passed'] for r in results)) + '/' + str(len(results)) + ' model cases passed; artifacts: ' + str(output), flush=True)
    return int(any(not r['passed'] for r in results))


if __name__ == '__main__':
    sys.exit(main())
