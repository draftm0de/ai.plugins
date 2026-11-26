#!/usr/bin/env python3
"""What the checks in scripts/verify/ share: reading repository files without following symlinks or running code. Managed by the plugin manager: do not edit."""
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


def kind_of(root, kind='auto'):
    """The checked kind of the repository root; ambiguous or mismatching roots are refused."""
    if not root.is_dir():
        raise ValueError('Repository directory does not exist')
    has_plugin = (root/'plugin.json').is_file()
    has_marketplace = (root/'marketplace.json').is_file()
    if kind == 'auto':
        if has_plugin == has_marketplace:
            raise ValueError('Cannot infer repository type; select --kind plugin or --kind marketplace and the exact repository root')
        return 'plugin' if has_plugin else 'marketplace'
    if kind == 'plugin' and not has_plugin:
        raise ValueError('--kind plugin requires a plugin repository root containing plugin.json')
    if kind == 'marketplace' and not has_marketplace:
        raise ValueError('--kind marketplace requires a marketplace repository root containing marketplace.json')
    return kind


def outcome(check, source, run):
    """One check as a result: what `run(root)` returns, or its findings."""
    root = Path(source).expanduser().resolve()
    try:
        return dict(run(root) or {}, valid=True, check=check, source=str(root), target_code_executed=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return {'valid': False, 'check': check, 'source': str(root), 'errors': [str(exc)], 'target_code_executed': False}
