# Teststruktur / Test structure

[Deutsch](#deutsch) · [English](#english) · [Entwicklung / Development](../docs/development.md)

## Deutsch

Die Tests prüfen die Werkzeuge und den Katalog dieses Marketplaces. Plugins werden in ihrem eigenen Repository getestet.

Tests sind zuerst nach Testart geordnet, darunter bei Bedarf nach Komponente. Python-Namen verwenden Unterstriche. Nur benötigte Verzeichnisse werden angelegt.

| Bereich | Aufgabe | Stand |
| --- | --- | --- |
| `unit/` | Einzelne Funktionen ohne Host oder Modell | vorhanden |
| `integration/` | Zusammenspiel von Werkzeugen und temporären Dateien | vorhanden |
| `contracts/` | Verträge für Manifest, Katalog und Pakete | vorhanden |
| `native/` | Echte Host-CLIs mit isolierten Profilen | noch keine Tests |
| `support/` | Gemeinsame Testhelfer ohne eigene Tests | vorhanden |

Im Stamm des Repositorys:

```sh
make test                # unit + integration + contracts
make test-unit
make test-integration
make test-contracts
make test-native         # nur ausdrücklich
python3 -B scripts/run_tests.py --kind deterministic --list
```

- `make test` führt nie native Tests aus, auch nicht bei gesetzten Umgebungsvariablen. Nur `make test-native` setzt `AI_PLUGIN_TEST_NATIVE`.
- Ein Bereich ohne Tests meldet `NOT RUN`. Das ist keine bestandene Prüfung.
- Mit `TEST_GROUP=<komponente>` wählst du ein Unterverzeichnis eines Bereichs. Derzeit gibt es keines. Eine Gruppe ohne Tests führt zum Fehlerstatus, ein Importfehler ebenso.
- Es werden keine Werkzeuge automatisch installiert.

Regressionen gehören zur jeweiligen Testart, nicht in einen eigenen Ordner. Testdaten bleiben fiktiv. CI führt `make test`, `make check-plugin` und `make verify` aus. Lokale Tests ersetzen keine Abnahme auf GitHub oder in der App.

## English

The tests check the tools and the catalogue of this marketplace. Plugins are tested in their own repositories.

Tests are organised by test type first, then by component where useful. Python names use underscores. Only needed directories are created.

| Layer | Purpose | State |
| --- | --- | --- |
| `unit/` | Individual functions without host or model | present |
| `integration/` | Tools and temporary files working together | present |
| `contracts/` | Manifest, catalogue and package contracts | present |
| `native/` | Real host CLIs with isolated profiles | no tests yet |
| `support/` | Shared test helpers without tests | present |

In the root of the repository:

```sh
make test                # unit + integration + contracts
make test-unit
make test-integration
make test-contracts
make test-native         # explicit only
python3 -B scripts/run_tests.py --kind deterministic --list
```

- `make test` never runs native tests, even when environment variables are set. Only `make test-native` sets `AI_PLUGIN_TEST_NATIVE`.
- A layer without tests reports `NOT RUN`. That is not a passed test.
- With `TEST_GROUP=<component>` you select a subdirectory of a layer. There is none yet. A group without tests fails, and so does an import error.
- Tools are never installed automatically.

Regressions belong to their test type, not to a separate folder. Fixtures stay fictional. CI runs `make test`, `make check-plugin` and `make verify`. Local tests do not replace acceptance on GitHub or in the app.
