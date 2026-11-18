# Development

**Deutsch** | [English](../en/development.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Kanonische Quelle

`skills/plugin-manager/` enthält Regeln, Laufzeit und kanonische Vorlagen. Root-`plugin.json` besitzt Identität und Host-Metadaten. `make sync-plugin` leitet die drei eingecheckten Host-Dateien ab; `make check-plugin` erkennt Drift ohne Schreiben. Fähigkeiten bleiben unter `skills/`, Assets unter `assets/`.

## Prüfungen

```sh
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

Verify führt keinen Zielcode aus. Es prüft neutrale Skill-Pfade, versionslose Importmetadaten, Vorlagenkopien, Ignore-Regeln, statische Python-Imports und Dokumentationsverweise. Eigene Funktionstests und Host-Abnahme bleiben nötig.

## Paketierung

### Lokal entwickeln

Führe die Befehle im Repository aus. Python 3, Make und die CLI des gewählten Hosts (`claude` beziehungsweise `codex`) müssen vorhanden sein.

1. Installiere deinen aktuellen Arbeitsstand einmal lokal:

   ```sh
   make install-local TARGET=claude
   # Alternativ für Codex:
   make install-local TARGET=codex
   ```

2. Übernimm nach Änderungen den neuen Arbeitsstand:

   ```sh
   make update-local TARGET=claude
   # Alternativ für Codex:
   make update-local TARGET=codex
   ```

3. Öffne eine neue lokale Sitzung und prüfe deine Änderung. Aktiviere nur die gewünschte Remote- oder Entwicklungskopie, damit gleichnamige Skills nicht doppelt angeboten werden.

Die Befehle erstellen einen gefilterten Stand unter `ai.plugins/dist/local-development/` und registrieren ihn über die Host-CLI als separaten Marketplace `draftmode-ai-plugins-dev`. Uncommittete Änderungen werden übernommen; Commit, Push und ZIP sind nicht nötig. Die automatisch erzeugte Hash-Kennung dient nur dem lokalen Cache und wird nicht ins Quellmanifest geschrieben. Checkout und Snapshot müssen während der Nutzung erhalten bleiben.

Mit `DRY_RUN=1` wird der lokale Snapshot erstellt und die Befehle werden angezeigt, ohne die Host-CLI aufzurufen. Beispiel: `make install-local TARGET=codex DRY_RUN=1`. Das verändert keine installierten Plugins.

Dieser Weg betrifft lokale Claude-Code- und Codex-Installationen. Der Import über eine Desktop- oder Web-Kontooberfläche bleibt ein eigener Vorgang; seine Synchronisierung ist damit nicht belegt. Kopiere keine Dateien manuell nach `~/.claude/plugins/cache`: Registrierung und Cache-Verwaltung übernimmt die Host-CLI. Persönliche bestehende Installationen werden durch unsere Tests nicht verändert; native Integrationstests verwenden temporäre Profile.

### Metadaten und Export

`make sync-plugin` aktualisiert die Host-Manifeste aus `plugin.json`; `make check-plugin` prüft sie ohne Änderungen. Die lokalen Make-Befehle delegieren an den gemeinsamen Marketplace. `install.sh` ist nur ein optionaler Durchreichaufruf, etwa `bash install.sh install-local --target claude`; es gibt keine Standardaktion.

Der reguläre Repository-Import erfolgt über die [Plugin-Verwaltung](installation.md). Plugin-ZIP-Bau und die bisherigen Make-Befehle `package`, `install` und `update` entfallen. Die Skill-Aktion **update** zur Dokumentationspflege bleibt erhalten. Der separate Website-Export bleibt verfügbar: `make check-docs-export` und `make export-docs`.

## CI und Releases

Die [CI](../../.github/workflows/validate.yml) prüft Tests, Repository-Metadaten und Dokumentation. Sie veröffentlicht nichts. Publish endet beim geprüften GitHub-Merge; es gibt keine Release-Actions, Tags oder Katalogpromotion. [Ablauf](publish.md) · [Nachweise](release-evidence.md).

## Dokumentation pflegen

Update pflegt die gewählten Sprachen aus aktuellen Quellen. Beispiel: `make init-plugin SOURCE=... OUTPUT=... LANGUAGES="de en" DEFAULT_LANGUAGE=de`. Optional: `PLUGIN_NAME=my-plugin REPOSITORY=https://github.com/OWNER/REPO AUTHOR="Bestätigter Herausgeber"`. Init erzeugt ein separates leeres Projekt; der Agent vervollständigt anschließend die Dokumentation. Website-Export bleibt bei seinem [Vertrag](../../skills/plugin-manager/references/export-contract.md).

Init verwendet einen bestätigten Plugin-Namen für `plugin.json` und beide Marketplace-Kataloge; lokale Entwicklung ergänzt `-dev`. Fehlt der Name oder ist er unklar, fragt der Agent vor Init nach. `PLUGIN_NAME` kann vom enthaltenen Skill-Namen abweichen; dessen Ordner und Frontmatter bleiben unverändert. Ohne Parameter verwendet das Hilfsskript den Quell-Skill-Namen.

Dieses Plugin liegt unter `plugins/plugin-manager/` im Repository `ai.plugins`. Der gemeinsame Marketplace heißt `draftmode-ai-plugins`. Seine Kataloge liegen an der Repository-Wurzel; dieses Plugin besitzt keinen eigenen eingecheckten Marketplace. Die Befehle oben gelten im Plugin-Ordner. Die wichtigsten Prüfungen und lokalen Installationsbefehle sind auch über das Root-Makefile verfügbar.

Die gemeinsame lokale Installation umfasst Manager und Interview Coach. `.local/marketplace.json` im Marketplace ordnet den Coach seinem lokalen Checkout zu; die entsprechende Datei im Coach zeigt zurück auf den Marketplace. Beide Dateien sind Git-ignoriert, Beispiele liegen als `local-marketplace.example.json` bei. `make install-local` und `make update-local` funktionieren aus beiden Repositories und aus dem gebündelten Manager-Ordner. Der gemeinsame Katalog enthält keine GitHub-Quellen, sondern gefilterte lokale Kopien.

Im Marketplace-Root: `make marketplace-verify`; für den Coach: `make plugin-verify SOURCE=../ai.plugin.interview-coach`. `make verify SOURCE=…` erkennt den Typ. Die Prüfung verändert keine Dateien und führt keinen Zielcode aus. Die alte interne Vorlagenprüfung `plugin_audit.py` bleibt für Scaffold-Tests vorhanden; sie ist nicht mehr die allgemeine Verify-Aktion.
