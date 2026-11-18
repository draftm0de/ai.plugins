# Draftmode AI Plugins

Marketplace für Claude und Codex. Repository: https://github.com/draftm0de/ai.plugins

| Plugin | Technischer Name | Quelle |
| --- | --- | --- |
| [Plugin Manager](plugins/plugin-manager/README.md) | `plugin-manager` | Lokal: `./plugins/plugin-manager` |
| [Interview Coach](https://github.com/draftm0de/ai.plugin.interview-coach) | `interview-coach` | Externes GitHub-Repository |

## Installation

Füge `https://github.com/draftm0de/ai.plugins` in der Plugin-Verwaltung als Marketplace hinzu und wähle **Plugin Manager** oder **Interview Coach**. Die Marketplace-Kennung ist `draftmode-ai-plugins`.

Claude Desktop: Einstellungen → Anpassungen → Plugins → + Hinzufügen → Marketplace hinzufügen → Aus einem Repository hinzufügen.

Codex: User Icon → Settings → Integration → Plugins → + Add → A Marketplace.

## Entwicklung

`marketplace.json` ist die kanonische Katalogkonfiguration. `make sync-plugin` erzeugt die Host-Kataloge und aktualisiert das Plugin-Manifest; `make check-plugin` prüft Drift.

```sh
make test
make verify
make validate-docs
make install-local TARGET=claude
# oder:
make install-local TARGET=codex
```

Nach lokalen Änderungen: `make update-local TARGET=claude` beziehungsweise `TARGET=codex`. Beide lokalen Plugins verwenden denselben Entwicklungs-Marketplace `draftmode-ai-plugins-dev`. [Entwicklerdokumentation](plugins/plugin-manager/docs/de/development.md).

Lokale IDE-Dateien, Caches, temporäre Dateien und `dist/` werden auf allen Ebenen ignoriert. Es werden keine ZIPs für die Plugin-Installation benötigt.

## Migration

Der aktuelle Arbeitsstand aus `zyris.skill.manager` wurde einschließlich uncommitteter Änderungen nach `plugins/plugin-manager` übernommen. Dieses Repository ist die neue kanonische Quelle. Das alte lokale Repository bleibt als Sicherung erhalten und wird nicht parallel weitergepflegt. Seine Git-Historie und persönlichen IDE-Einstellungen wurden nicht kopiert.

Die technische Plugin-Identität hat sich zu `plugin-manager` geändert. Bestehende Installationen werden dadurch nicht automatisch umbenannt. Installiere den neuen Eintrag und deaktiviere anschließend die alte Kopie. Die bisherige Bestätigung des alten Imports ist kein Abnahmetest dieses Marketplaces.

## Test mit zwei Plugins

1. Zuerst den neuen Stand von `draftm0de/ai.plugin.interview-coach` veröffentlichen.
2. Danach die Katalogänderung in diesem Repository veröffentlichen.
3. **Draftmode AI Plugins** in Claude bzw. Codex synchronisieren.
4. Prüfen, dass **Plugin Manager** und **Interview Coach** angeboten werden, und den Coach installieren.

Der Coach besitzt keinen eigenen Marketplace. Sein Repository wird über den Default-Branch ohne Tag oder Versionsbindung referenziert. Der Zugriff auf beide Repositories muss möglich sein. Der gemeinsame lokale Entwicklungs-Marketplace enthält die Arbeitsstände beider Plugins. Die Create-/Configure-Aktionen werden separat weiterentwickelt.

## Lokale Zuordnung und Prüfung

Auf diesem Rechner sind die Zuordnungen bereits in `.local/marketplace.json` eingerichtet. Diese Datei bleibt Git-ignoriert. Auf einem neuen Rechner `local-marketplace.example.json` nach `.local/marketplace.json` kopieren und den Coach-Pfad anpassen; relative Pfade beziehen sich auf die Marketplace-Wurzel. Im Coach-Repository zeigt dessen eigene `.local/marketplace.json` zurück auf diesen Marketplace.

`make install-local TARGET=claude` oder `TARGET=codex` funktioniert im Marketplace- und im Coach-Repository. Beide Aufrufe installieren **beide Plugins** aus den lokalen Arbeitsständen im selben Katalog. `make update-local` erneuert beide Snapshots. `DRY_RUN=1` erstellt nur Snapshots und zeigt die Befehle. Es werden keine ZIPs oder GitHub-Updates benötigt und keine persönlichen Plugins durch unsere Tests verändert.

```sh
make marketplace-verify
make plugin-verify SOURCE=../ai.plugin.interview-coach
make verify SOURCE=../ai.plugin.interview-coach
```

`verify` erkennt den Repository-Typ. Die expliziten Aktionen lehnen den falschen Typ ab. Alle Prüfungen lesen nur Dateien; entfernte Repository-Inhalte und Host-Abnahme werden nicht als geprüft ausgegeben. Bei der Skill-Ausführung ist das Benutzerprojekt der Zielordner, niemals automatisch das Installationsverzeichnis des Managers.

- `plugin-verify`: Plugin-Identität, Skills und Host-Manifeste prüfen.
- `marketplace-verify`: Kataloge, lokale Plugins und externe Verweise prüfen.
- `configure` würde Konfiguration schreiben oder reparieren; diese Aktion ist noch nicht implementiert.
- `plugin-create` und `marketplace-create` sind als getrennte spätere Aktionen vorgesehen.

Nach Installation eine neue lokale Host-Sitzung öffnen. Nur die gewünschte reguläre oder Entwicklungskopie eines Plugins aktivieren. Frühere `plugin-manager-dev`-Installationen werden nicht automatisch gelöscht; entferne/deaktiviere sie nach erfolgreicher Gegenprobe. Die CLI-Installation belegt keine automatische Synchronisierung in eine Desktop-/Web-Kontooberfläche.
