#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Only explicit local-development and metadata commands are supported.
exec "${PYTHON:-python3}" "$ROOT/scripts/plugin.py" "$@"
