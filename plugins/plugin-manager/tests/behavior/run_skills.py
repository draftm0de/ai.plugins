#!/usr/bin/env python3
"""Opt-in prompt-only model evaluations of the Manager skills (setup, docs, modify, publish).

The model gets the real skill texts, the output of the helper commands the skill starts with (fictional, already
run) and the conversation so far. It has no tools and answers with what it would say and run next. The grading is
deterministic. This checks that the instruction texts steer a model correctly; it does not test host routing
(/plugin-manager:<skill>), which needs a host (make test-native / install-local)."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
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
spec = importlib.util.spec_from_file_location('run_review_shared', ROOT / 'tests/behavior/run_review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

STRING = {'type': 'string'}
SCHEMA = review.object_schema({
    'reply': STRING,
    'commands': {'type': 'array', 'items': STRING},
    'next_step': {'type': 'string', 'enum': ['reports_only', 'asks_question', 'asks_confirmation']},
    'writes': {'type': 'boolean'},
})
ENGLISH = {'the', 'and', 'is', 'not', 'to', 'of', 'this', 'run', 'first', 'please', 'before', 'with', 'was', 'are', 'it', 'you'}
GERMAN = {'der', 'die', 'das', 'und', 'ist', 'nicht', 'zu', 'bitte', 'zuerst', 'vor', 'mit', 'wurde', 'sind', 'es', 'sie', 'noch', 'bevor', 'kann'}


def words(text):
    return re.findall(r"[a-zäöüß]+", text.casefold())


def language_of(text):
    tokens = words(text)
    english, german = sum(w in ENGLISH for w in tokens), sum(w in GERMAN for w in tokens)
    return 'de' if german > english else 'en' if english > german else 'unknown'


def load_source(spec_text):
    path, _, marker = spec_text.partition('#')
    text = (ROOT / path).read_text(encoding='utf-8')
    if not marker:
        return path, text
    start = text.index(marker)
    end = text.find('\n- **', start + 1)
    return path + ' (excerpt: ' + marker + ')', text[start:end if end != -1 else None]


def build_prompt(case):
    sources = '\n\n'.join('--- ' + name + ' ---\n' + text for name, text in map(load_source, case['sources']))
    observed = '\n\n'.join('$ ' + o['command'] + '\n' + o['output'] for o in case['observed'])
    history = '\n'.join(item['role'].upper() + ': ' + item['text'] for item in case['history'])
    return ('You are the agent that has just loaded the Plugin Manager skill below. All tools are unavailable: you cannot run '
            'commands or write files. Say what you would write to the person and which shell commands you would run next, in order. '
            'The helper commands the skill starts with have already been run for you; their output is below and is real. '
            'Follow the skill and its shared rules exactly; do not invent results of commands you have not been given. '
            'Return only one JSON object matching the schema: reply (what you write to the person now), commands (shell commands you '
            'would run now, possibly none), next_step (reports_only: you only report; asks_question: you end by asking a question; '
            'asks_confirmation: you end by asking for an explicit yes), writes (true only if your commands change files).\n\n'
            'SKILL TEXTS:\n' + sources + '\n\nHELPER OUTPUT ALREADY OBSERVED:\n' + observed + '\n\nCONVERSATION SO FAR:\n' + history)


def grade(case, report):
    expect, errors = case['expect'], []
    reply, commands = report.get('reply', ''), report.get('commands', [])
    if not isinstance(reply, str) or not reply.strip():
        return ['empty reply']
    if 'language' in expect and language_of(reply) != expect['language']:
        errors.append('reply is not in ' + expect['language'])
    for needle in expect.get('mentions', []):
        if needle.casefold() not in reply.casefold():
            errors.append('reply does not mention ' + needle)
    if expect.get('mentions_any') and not any(n.casefold() in reply.casefold() for n in expect['mentions_any']):
        errors.append('reply mentions none of ' + ', '.join(expect['mentions_any']))
    if 'next_step' in expect and report.get('next_step') != expect['next_step']:
        errors.append('next_step is ' + str(report.get('next_step')) + ', expected ' + expect['next_step'])
    if 'writes' in expect and report.get('writes') is not expect['writes']:
        errors.append('writes is ' + str(report.get('writes')) + ', expected ' + str(expect['writes']))
    if 'max_questions' in expect and reply.count('?') > expect['max_questions']:
        errors.append('more than ' + str(expect['max_questions']) + ' question(s)')
    for pattern in expect.get('required_commands', []):
        if not any(re.search(pattern, c) for c in commands):
            errors.append('missing command matching ' + pattern)
    for pattern in expect.get('forbidden_commands', []):
        if any(re.search(pattern, c) for c in commands):
            errors.append('forbidden command matching ' + pattern)
    return errors


def run_case(cli, case, output, timeout):
    output.mkdir(parents=True, exist_ok=False)
    prompt = build_prompt(case)
    (output / 'prompt.txt').write_text(prompt)
    with tempfile.TemporaryDirectory(prefix='fictional-skill-') as directory:
        work = Path(directory).resolve()
        schema_file, response = work / 'schema.json', work / 'response.json'
        schema_file.write_text(json.dumps(SCHEMA))
        started = datetime.now(timezone.utc).isoformat()
        try:
            proc = subprocess.run(review.command(cli, schema_file, response, SCHEMA), input=prompt, cwd=work, text=True,
                                  capture_output=True, timeout=timeout, check=False)
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = 124, (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or ''), ''
        (output / 'stdout.jsonl').write_text(stdout)
        (output / 'stderr.txt').write_text(stderr)
        errors, report, metadata = [], None, {}
        if code:
            errors.append('CLI exit code ' + str(code))
        try:
            if cli == 'claude':
                envelope = json.loads(stdout)
                metadata = {'model_usage': envelope.get('modelUsage'), 'cost_usd': envelope.get('total_cost_usd')}
                if envelope.get('is_error'):
                    errors.append('Claude reported an error')
                report = envelope.get('structured_output') or review.parse_report(envelope.get('result', ''))
            else:
                report = review.parse_report(response.read_text())
                for line in stdout.splitlines():
                    item = json.loads(line).get('item', {})
                    if item.get('type') in ('command_execution', 'mcp_tool_call', 'web_search', 'file_change'):
                        errors.append('unexpected tool use: ' + item['type'])
            errors += grade(case, report)
        except (ValueError, TypeError, AttributeError, KeyError, OSError) as exc:
            errors.append('Invalid/missing model answer: ' + str(exc))
    result = {'case': case['id'], 'cli': cli, 'started_at': started, 'exit_code': code, 'errors': errors, 'passed': not errors,
              'report': report, 'metadata': metadata, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'limitations': ['Prompt-only evaluation of the skill texts; no host routing, no tool use.']}
    (output / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', choices=['claude', 'codex'])
    parser.add_argument('--case')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    cases = json.loads(CASES.read_text())
    if args.case:
        cases = [c for c in cases if c['id'] == args.case]
    if not cases:
        parser.error('unknown case')
    if args.list:
        for case in cases:
            print(case['id'])
        return 0
    if not args.cli:
        parser.error('--cli required')
    if not shutil.which(args.cli):
        parser.error('CLI unavailable; no automatic installation')
    output = (args.output_dir or ROOT / '.tmp/tests/behavior/skills' / args.cli / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'cli-version.txt').write_text(subprocess.run([args.cli, '--version'], text=True, capture_output=True).stdout)
    results = []
    for case in cases:
        result = run_case(args.cli, case, output / case['id'], args.timeout)
        results.append(result)
        print(('PASS ' if result['passed'] else 'FAIL ') + case['id'] + ': ' + '; '.join(result['errors']), flush=True)
    (output / 'summary.json').write_text(json.dumps({'results': results}, indent=2, ensure_ascii=False) + '\n')
    print(str(sum(r['passed'] for r in results)) + '/' + str(len(results)) + ' skill checks passed; artifacts: ' + str(output), flush=True)
    return int(any(not r['passed'] for r in results))


if __name__ == '__main__':
    sys.exit(main())
