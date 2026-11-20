"""Project-scoped operator preference; no global state or language inference."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile


def preference(root, language=None):
    root = Path(root).absolute()
    path = root / '.project' / 'operator.json'
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Operator preference path must not contain symlinks')
    if not root.is_dir():
        raise ValueError('Select an existing project directory')
    current = None
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(data, dict) or set(data) != {'schema_version', 'operator_language'}
                or type(data['schema_version']) is not int or data['schema_version'] != 1):
            raise ValueError('Unsupported operator preference format; existing data preserved')
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
        raise ValueError('Use a language tag such as de, en or pt-BR; existing data preserved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--set', dest='language', help='Only an explicitly selected operator language')
    args = parser.parse_args()
    try:
        print(json.dumps(preference(args.root, args.language)))
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
