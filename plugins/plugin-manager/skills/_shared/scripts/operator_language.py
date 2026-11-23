"""Project-scoped operator preference; no global state or language inference."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


class OperatorLanguageError(ValueError):
    """A failure of this helper with a catalogue code (messages_base.BASE_CATALOGUE) and the facts of its wording."""

    def __init__(self, code, **facts):
        super().__init__(code)
        self.code = code
        self.facts = facts


def preference(root, language=None):
    root = Path(root).absolute()
    path = root / '.project' / 'operator.json'
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise OperatorLanguageError('LANGUAGE_PATH_UNSAFE', path=str(path))
    if not root.is_dir():
        raise OperatorLanguageError('LANGUAGE_PROJECT_MISSING')
    if path.parent.exists() and not path.parent.is_dir():
        raise OperatorLanguageError('LANGUAGE_PATH_CONFLICT', path=str(path.parent))
    current = None
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            raise OperatorLanguageError('LANGUAGE_FORMAT_UNSUPPORTED', path=str(path)) from None
        if (not isinstance(data, dict) or set(data) != {'schema_version', 'operator_language'}
                or type(data['schema_version']) is not int or data['schema_version'] != 1):
            raise OperatorLanguageError('LANGUAGE_FORMAT_UNSUPPORTED', path=str(path))
        current = data['operator_language']
        validate_language(current)
    if language is None:
        return {'operator_language': current, 'needs_choice': current is None}
    validate_language(language)
    if current != language:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.operator-', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
                json.dump({'schema_version': 1, 'operator_language': language}, handle, indent=2)
                handle.write('\n')
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {'operator_language': language, 'needs_choice': False}


def validate_language(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', value):
        raise OperatorLanguageError('LANGUAGE_TAG_INVALID')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--set', dest='language', help='Only an explicitly selected operator language')
    parser.add_argument('--skill', help='The skill that calls this helper; named in a failure message')
    parser.add_argument('--message-language', help='Language of a failure message (the language of the person\'s text); default English')
    args = parser.parse_args()
    try:
        print(json.dumps(preference(args.root, args.language)))
    except (ValueError, OSError) as exc:
        sys.path.insert(0, str(Path(__file__).resolve().parent))  # the entry file locates its own scripts folder
        from messages_base import BASE_CATALOGUE, plugin_name_from, render_failure
        code, facts = (exc.code, exc.facts) if isinstance(exc, OperatorLanguageError) else ('UNKNOWN', {})
        parser.exit(1, render_failure(BASE_CATALOGUE, code, args.message_language, plugin_name_from(__file__), args.skill, **facts) + '\n')


if __name__ == '__main__':
    main()
