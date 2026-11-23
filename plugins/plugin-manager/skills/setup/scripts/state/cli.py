"""Command line of the setup state helper."""
import argparse
import json
from .context import Context
from . import preferences
from . import messages
from . import recording
from . import reporting
from . import skeleton
from . import syncing
from .constants import Conflict


def conflict_of(result):
    """The first conflict of a failed answer as an object `messages.explain` can classify."""
    entry = (result.get('conflicts') or [{}])[0]
    return Conflict(entry.get('path', '.'), entry.get('reason', ''), entry.get('code'))


def main(argv=None, source_root=None, manager_root=None):
    """Command line. source_root/manager_root are for code callers (tests with mock data); the command line has no such option."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    read = commands.add_parser('status', help='Write-free inspection of language and development files')
    add = commands.add_parser('setup', help='Add missing files, ignore rule, language and ownership lock')
    only = commands.add_parser('language', help='Fresh folder without plugin.json: save the operator language')
    only.add_argument('--language', required=True, help='Explicitly selected operator language tag')
    mark = commands.add_parser('record', help='Write the configuration evidence after a successful configuration run')
    mark.add_argument('--kind', required=True, help='Configured kind (a directory with a manifest under templates/, for the Manager plugin or marketplace)')
    mark.add_argument('--artifact', required=True, help='Name of the created plugin or marketplace')
    closed = commands.add_parser('gate', help='Write-free: is the workpackage ready for a writing skill other than setup (exit 1 if not)')
    closed.add_argument('--action', choices=('docs', 'modify', 'publish'), help='The gated skill; names it in the stop message')
    closed.add_argument('--message-language', choices=messages.LANGUAGES, help='Language of the message: the language of the person\'s text; default the saved operator language, else English')
    unknown = commands.add_parser('explain', help='Write-free: the finished message for an error no command reported (cause not known)')
    unknown.add_argument('--action', required=True, choices=tuple(messages.ACTIONS), help='What the person asked for')
    unknown.add_argument('--message-language', choices=messages.LANGUAGES)
    unknown.add_argument('--error', default='', help='The raw error text; it is kept as detail and never put into the message')
    decide = commands.add_parser('sync', help='Apply one explicit keep/adopt decision for a deviating managed file')
    decide.add_argument('--decision', required=True, choices=('keep', 'adopt', 'delete'), help='keep: keep local file; adopt: take template (content question); delete: remove the file (removal question)')
    decide.add_argument('--path', required=True, help='Managed file path from status sync.decisions')
    decide.add_argument('--source-hash', required=True, help='source_hash shown by status for this decision, or the literal removed for a removal question')
    decide.add_argument('--local-hash', required=True, help='local_hash shown by status for this decision')
    for sub in (read, closed, add, only, decide, mark):
        sub.add_argument('--target', required=True, help='Explicitly selected folder')
        sub.add_argument('--plugin', required=True, help='Name of the running plugin that owns the evidence (for example plugin-manager)')
    add.add_argument('--language', help='Explicitly selected operator language tag (de, en, pt-BR)')
    args = parser.parse_args(argv)
    if args.operation == 'explain':
        said = messages.explain(args.action, RuntimeError(args.error), args.message_language)
        print(json.dumps({'operation': 'explain', 'ok': True, 'message': said['message'], 'known': said['known'], 'detail': said['detail']}, indent=2, ensure_ascii=False))
        return 0
    try:
        ctx = Context(args.plugin, source_root, manager_root)
        result = {'status': lambda: reporting.status(ctx, args.target), 'gate': lambda: reporting.gate(ctx, args.target, args.action, args.message_language), 'record': lambda: recording.record(ctx, args.target, args.kind, args.artifact), 'setup': lambda: skeleton.setup(ctx, args.target, args.language),
                  'language': lambda: preferences.language_only(ctx, args.target, args.language),
                  'sync': lambda: syncing.sync(ctx, args.target, args.decision, args.path, args.source_hash, args.local_hash)}[args.operation]()
    except Conflict as conflict:
        result = reporting.conflict_result(args.operation, args.target, conflict)
    except OSError as exc:  # expected filesystem failures outside the write phase
        conflict = Conflict('.', 'Filesystem error: ' + (exc.strerror or str(exc)))
        result = reporting.conflict_result(args.operation, args.target, conflict)
    if not result['ok'] and result.get('operation') != 'gate':
        said = messages.explain(args.operation if args.operation in messages.ACTIONS else 'setup', conflict_of(result), messages.language_for(args.target, getattr(args, 'language', None)), folder=args.target)
        result['message'] = said['message']
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1
