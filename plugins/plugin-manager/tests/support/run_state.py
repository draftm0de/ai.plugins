"""Test driver: runs the REAL setup state command line in isolated mode with mock data given as a context.

Usage: python3 -B -I run_state.py <scripts-dir> <source-root|-> <manager-root|-> <cli arguments...>
The production command line has no option for the data root; this driver passes it in code, like an in-process test."""
import sys
from pathlib import Path

scripts, source_root, manager_root, *argv = sys.argv[1:]
sys.dont_write_bytecode = True
sys.path.insert(0, scripts)

from state import main  # noqa: E402

sys.exit(main(argv, None if source_root == '-' else Path(source_root), None if manager_root == '-' else Path(manager_root)))
