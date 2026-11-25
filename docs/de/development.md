# Entwicklung

[Installation](installation.md) · [Plugins](plugins.md) · [Begriffe](concepts.md)

Für alle, die an diesem Marketplace arbeiten. Zum Benutzen brauchst du diese Seite nicht.

## Voraussetzungen

- Git und Python 3.10 oder neuer. Make ist optional.
- Claude oder Codex mit installiertem Plugin Manager.
- Für die lokale Installation die jeweilige CLI (`claude` oder `codex`).
- Je ein GitHub-Repository für den Marketplace und für jedes Plugin, jeweils lokal geklont.

## Einrichten

1. Marketplace-Repository auf GitHub anlegen und klonen.
2. Darin `/plugin-manager:setup` ausführen und „Marketplace“ wählen.
3. Plugin-Repository anlegen und klonen, darin `/plugin-manager:setup` ausführen, „Plugin“ wählen und diesen Marketplace nennen. Der Eintrag in `marketplace.json` und die lokale Zuordnung entstehen dabei.

## Lokal testen

Im Marketplace-Ordner:

```bash
make install-local TARGET=claude
```

Das installiert die lokalen Stände aller gelisteten Plugins als eigenen Entwicklungs-Marketplace `<name>-dev`, auch nicht committete Änderungen. Danach eine neue Sitzung öffnen. Für Codex `TARGET=codex`.

## Befehle

Alle Befehle laufen im Stamm des Repositorys. `make help` listet sie auch.

| Befehl | Zweck | Variablen |
| --- | --- | --- |
| `make sync` | Host-Kataloge aus `marketplace.json` erzeugen | |
| `make check` | Prüfen, ob die Host-Kataloge dazu passen | |
| `make test` | Deterministische Tests | `TEST_GROUP=<name>`: nur eine Komponente |
| `make verify` | Struktur nur lesend prüfen | `SOURCE=<ordner>`; `REVIEW=1`: zusätzlich Abgleich mit `SCOPE.md` |
| `make install-local` | Lokale Plugin-Stände installieren | `TARGET=claude` oder `codex`; `DRY_RUN=1`: nur Pakete bauen |
| `make help` | Befehle anzeigen | |

Eigene Befehle stehen in `CUSTOM.mk`.

## CI

`.github/workflows/dm-verify.yml` läuft bei jedem Push, jedem Pull Request und auf Knopfdruck. Rot wird der Lauf, wenn ein Schritt fehlschlägt.

| Schritt | Rot, wenn |
| --- | --- |
| `python3 -B scripts/run_tests.py` | ein Test fehlschlägt |
| `python3 -B scripts/marketplace.py check` | die Host-Kataloge nicht zu `marketplace.json` passen |
| `python3 -B scripts/verify.py --source . --kind marketplace` | Katalog oder Struktur ungültig sind, `SCOPE.md` oder `AGENTS.md` abweichen oder der Doku Seiten, Überschriften oder Linkziele fehlen |

Eigene Schritte stehen in einer weiteren Datei unter `.github/workflows/`. Lokal prüfst du dasselbe mit `make test check verify`.

## Gemeinsame Dateien

Plugin Manager hält einen Teil der Dateien aktuell (Sync), andere legt er nur einmal an (Seed). `.project/plugins/plugin-manager/skeleton.json` listet die Sync-Dateien. Ändere sie nicht: Eigene Regeln gehören in `CUSTOM.AGENTS.md`, eigene Befehle in `CUSTOM.mk`, eigene CI-Schritte in eine weitere Datei unter `.github/workflows/`. Änderst du eine Sync-Datei doch, fragt `/plugin-manager:setup`, ob du sie behältst oder die Vorlage übernimmst. Behältst du `AGENTS.md`, `SCOPE.md` eines Marketplace oder einen Standard unter `docs/standards/`, schlägt `verify` fehl.

## Veröffentlichen

Zuerst die Plugins committen und pushen, dann den Marketplace:

```bash
make sync
```

```bash
make check test verify
```

Installiert wird, was auf dem Standard-Branch liegt. Es gibt keine Versionen, Tags oder Releases. Wer den Marketplace schon nutzt, aktualisiert ihn wie unter [Installation](installation.md) beschrieben.
