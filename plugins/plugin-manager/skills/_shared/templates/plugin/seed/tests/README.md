# Tests / Tests

Use `make test` for deterministic unit, integration and contract checks. `make test-unit`, `make test-integration` and `make test-contracts` select a layer. `make test-native` is separate and requires isolated host profiles; `make test-behavior` is only for explicitly authorized model tests. Missing suites report `NOT RUN`, not acceptance. No model or host test is included by default.

`make test` prüft deterministische Unit-, Integrations- und Vertragstests. Einzelbereiche: `make test-unit`, `make test-integration`, `make test-contracts`. Native Host- und Modelltests sind ausdrücklich getrennt. Fehlende Suiten melden `NOT RUN`, keine erfolgreiche Abnahme.

Place tests under `tests/unit/`, `tests/integration/`, `tests/contracts/`, `tests/native/` or `tests/behavior/`, with optional skill/component subdirectories. Add `__init__.py` to discovered unittest directories. Fictional data belongs under `tests/fixtures/`, helpers under `tests/support/`. Create only needed directories. The scaffold provides structural contract checks only; add actual product tests before claiming behavior acceptance.

Tests nach Testart und bei Bedarf nach Skill/Komponente ablegen. In unittest-Verzeichnissen `__init__.py` ergänzen. Fiktive Daten: `tests/fixtures/`; Helfer: `tests/support/`. Nur benötigte Ordner anlegen. Das Gerüst enthält ausschließlich Strukturverträge; Produktverhalten benötigt eigene Tests.
