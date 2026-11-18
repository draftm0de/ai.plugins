"""Materialize filtered host files in isolation without archives or host registration."""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def materialize(destination, host='codex'):
    spec = importlib.util.spec_from_file_location('fixture_engine', ROOT/'scripts/plugin.py')
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    _, portable, claude = engine.payload()
    files = claude if host == 'claude' else engine.codex_payload(portable)
    for relative, content in files.items():
        path = Path(destination)/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return Path(destination)
