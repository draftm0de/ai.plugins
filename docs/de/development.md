# Entwicklung

**Deutsch** | [English](../en/development.md)

[Start](../../README.md) · [Installation](installation.md) · [Begriffe](concepts.md) · [Entwicklung](development.md)

Für alle, die an diesem Marketplace arbeiten. Zum Benutzen brauchst du diese Seite nicht.

## Voraussetzungen

- Git und Python 3.10 oder neuer. Make ist optional.
- Claude oder Codex mit installiertem Plugin Manager.
- Für die lokale Installation die jeweilige CLI (`claude` oder `codex`).
- Je ein GitHub-Repository für den Marketplace und für jedes Plugin, jeweils lokal geklont.

## Einrichten

### Marketplace

Ein Marketplace ist ein eigenes Repository. Lege es auf GitHub an, klone es und öffne den Ordner. Rufe dort `/plugin-manager:setup` auf und wähle „Marketplace“. Er fragt dich unter anderem nach Name und Eigentümer. Danach liegen der Katalog `marketplace.json` und die gemeinsamen Dateien in deinem Repository.

### Plugins aufnehmen

Jedes Plugin bekommt sein eigenes Repository. Lege es an, klone es, öffne den Ordner und rufe `/plugin-manager:setup` auf. Wähle „Plugin“ und nenne den Ordner dieses Marketplace.

Dabei entstehen der Eintrag in `marketplace.json` und die lokale Zuordnung, mit der du die Plugins später auf deinem Rechner testest. Committen und pushen machst du selbst, in beiden Repositorys.

Gibt es das Plugin schon, öffne seinen Ordner, rufe `/plugin-manager:setup` auf und bitte darum, es mit diesem Marketplace zu verbinden. Ein Plugin gehört immer zu genau einem Marketplace.

## Lokal testen

Der Marketplace ist der Ort, aus dem Claude und Codex installieren; die Plugins selbst liegen in eigenen Repositorys. Zum Testen baut er aus den Ordnern auf deinem Rechner einen eigenen Entwicklungs-Marketplace `<name>-dev` und installiert daraus. Wo die Plugins liegen, steht in der lokalen Zuordnung, die `:setup` anlegt. Fehlt der Ordner eines gelisteten Plugins, bricht er ab, bevor er etwas installiert.

Du brauchst nur einen Befehl, im Ordner des Marketplace:

```bash
make install-local TARGET=claude
```

Für Codex nimmst du `TARGET=codex`. Mit `DRY_RUN=1` baut er nur die Pakete und installiert nichts. Öffne danach eine neue Sitzung. Auch nicht committete Änderungen sind dabei. Vorher musst du nichts erzeugen oder prüfen; das machst du, bevor du veröffentlichst.

## Befehle

`marketplace.json` ist die eine Datei, die du pflegst: der Name des Marketplace und die Liste seiner Plugins. Claude und Codex lesen jeweils einen eigenen **Host-Katalog**, `.claude-plugin/marketplace.json` und `.agents/plugins/marketplace.json`. Beide werden aus `marketplace.json` erzeugt; du bearbeitest sie nie von Hand.

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
| `python3 -B scripts/verify/structure.py --source .` | Manifeste, Kataloge, Skills oder die Struktur ungültig sind |
| `python3 -B scripts/verify/standards.py --source .` | `SCOPE.md` oder `AGENTS.md` abweichen |
| `python3 -B scripts/verify/docs.py --source .` | nie: fehlende Seiten, Überschriften oder Linkziele der Doku sind nur Warnungen |

Eigene Schritte stehen in einer weiteren Datei unter `.github/workflows/`. Lokal prüfst du dasselbe mit `make test check verify`.

## Veröffentlichen

Zuerst die Plugins committen und pushen, dann den Marketplace:

```bash
make sync
```

```bash
make check test verify
```

Installiert wird, was auf dem Standard-Branch liegt. Es gibt keine Versionen, Tags oder Releases. Wer den Marketplace schon nutzt, aktualisiert ihn wie unter [Installation](installation.md) beschrieben.

<hr>

Diese Seite wird automatisch über `/plugin-manager:docs` erstellt. Ändere sie nicht von Hand.
