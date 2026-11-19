# Teststruktur / Test structure

Tests sind zuerst nach Testart, darunter bei Bedarf nach Skill oder Komponente geordnet. Python-Namen verwenden Unterstriche (`plugin_create`). Nur benötigte Verzeichnisse werden angelegt.

Tests are organized by test type first, then by skill or component where useful. Python names use underscores (`plugin_create`). Only needed directories are created.

| Bereich / Layer | Aufgabe / Purpose |
| --- | --- |
| `unit/` | Einzelne Funktionen ohne Host oder Modell / Individual functions without host or model |
| `integration/` | Zusammenspiel von Werkzeugen, Dateien und temporären Repositories / Tools, files and temporary repositories working together |
| `contracts/` | Skill-, Manifest-, Katalog- und Paketverträge / Skill, manifest, catalog and package contracts |
| `behavior/` | Ausdrücklich gestartete Modelltests / Explicit model behavior tests |
| `native/` | Echte Host-CLIs mit isolierten Profilen / Real host CLIs with isolated profiles |
| `fixtures/` | Fiktive Testdaten / Fictional test data |
| `support/` | Gemeinsame Testhelfer ohne eigene Tests / Shared test helpers without tests |

Im jeweiligen Repository / From the relevant repository:

```sh
make test                    # unit + integration + contracts
make test-unit
make test-integration
make test-contracts
make test-native             # explicit, isolated hosts only
make test-behavior           # explicit model calls, when configured
python3 -B scripts/run_tests.py --kind deterministic --list
```

`make test` führt auch bei gesetzten Umgebungsvariablen keine nativen Tests aus. Ein nicht vorhandener Bereich meldet ausdrücklich `NOT RUN`; das ist keine bestandene Prüfung. Ein unbekannter `TEST_GROUP` oder Importfehler führt zum Fehlerstatus. Es werden keine Werkzeuge automatisch installiert.

`make test` never runs native tests, regardless of environment flags. An absent layer reports `NOT RUN`, which is not a passed test. Unknown `TEST_GROUP` values or import errors fail. Tools are never installed automatically.

Im Manager kann `make test TEST_GROUP=publish` oder `make test-integration TEST_GROUP=plugin-create` eine Komponente auswählen. `make test-native` im ai.plugins-Stamm führt die Marketplace- und Manager-Hosttests aus. Native Tests verändern keine persönlichen Installationen. Der Coach hat derzeit keine eigene native Suite; seine Host-Abnahme bleibt separat. Der Manager besitzt Review-Modelltests über `make test-behavior CLI=claude|codex`. Der Coach besitzt Coaching-Modelltests und zusätzlich `make test-journey CLI=claude`. Modelltests können Credits verbrauchen; sie werden nicht mit dem normalen Testlauf gestartet.

In the Manager, `make test TEST_GROUP=publish` or `make test-integration TEST_GROUP=plugin-create` selects a component. Root `make test-native` in ai.plugins runs marketplace and Manager host tests. Native tests never change personal installations. The Coach currently has no dedicated native suite; host acceptance remains separate. The Manager has review model tests via `make test-behavior CLI=claude|codex`. The Coach has coaching model tests and also `make test-journey CLI=claude`. Model tests may consume credits and never run with the default suite.

Regressionen gehören zur jeweiligen Testart, nicht in einen eigenen regression-Ordner. CI verwendet weiterhin `make test`. Testdaten bleiben fiktiv; Modellartefakte liegen ignoriert unter `.tmp/tests/`. Erfolgreiche lokale Tests ersetzen keine veröffentlichte GitHub-/GUI-Abnahme.

Regressions belong to their test type rather than a separate regression directory. CI continues to use `make test`. Fixtures remain fictional; model artifacts stay ignored under `.tmp/tests/`. Local success does not certify published GitHub/GUI acceptance.

Native selection uses only `--kind native` / `make test-native`; the runner sets `AI_PLUGIN_TEST_NATIVE`. Previous native gate names are not consumed.
