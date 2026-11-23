#!/usr/bin/env python3
"""Check and set up the workpackage of a selected folder for one running plugin (--plugin).

Configuration evidence (.project/plugins/<plugin>/config.json) and skeleton ownership evidence
(.project/plugins/<plugin>/skeleton.json) are kept per running plugin. Existing regular files are never
updated without an explicit sync decision. Writes are limited to missing files/directories, one ignore rule,
the operator preference (through operator_language.py), the configuration evidence and the skeleton evidence.

Thin entry: the logic lives in the package next to this file (state/). Isolated mode (-I) does not put this
folder on the import path, so it is added explicitly.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from state import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
