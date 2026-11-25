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
