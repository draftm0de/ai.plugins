<!-- Managed by the plugin manager: do not edit. -->

# Tests / Tests

Use `make test` for the deterministic unit, integration and contract checks; `make test TEST_GROUP=<name>` selects a component. Other layers run directly: `python3 -B scripts/run_tests.py --kind unit|integration|contracts|native`. Missing suites report `NOT RUN`, not acceptance.

`make test` prüft deterministische Unit-, Integrations- und Vertragstests; `make test TEST_GROUP=<name>` wählt eine Komponente. Andere Ebenen direkt: `python3 -B scripts/run_tests.py --kind unit|integration|contracts|native`. Fehlende Suiten melden `NOT RUN`, keine erfolgreiche Abnahme.

Place tests under `tests/unit/`, `tests/integration/`, `tests/contracts/`, `tests/native/` or `tests/behavior/`, with optional skill/component subdirectories. Add `__init__.py` to discovered unittest directories. Fictional data belongs under `tests/fixtures/`, helpers under `tests/support/`. Create only needed directories. The scaffold provides structural contract checks only; add actual product tests before claiming behavior acceptance.

Tests nach Testart und bei Bedarf nach Skill/Komponente ablegen. In unittest-Verzeichnissen `__init__.py` ergänzen. Fiktive Daten: `tests/fixtures/`; Helfer: `tests/support/`. Nur benötigte Ordner anlegen. Das Gerüst enthält ausschließlich Strukturverträge; Produktverhalten benötigt eigene Tests.
