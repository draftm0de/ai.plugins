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

Nach lokalen Änderungen: `make update-local TARGET=claude` beziehungsweise `TARGET=codex`. Die lokale Entwicklungskopie des Managers verwendet `plugin-manager-dev`. [Entwicklerdokumentation](plugins/plugin-manager/docs/de/development.md).

Lokale IDE-Dateien, Caches, temporäre Dateien und `dist/` werden auf allen Ebenen ignoriert. Es werden keine ZIPs für die Plugin-Installation benötigt.

## Migration

Der aktuelle Arbeitsstand aus `zyris.skill.manager` wurde einschließlich uncommitteter Änderungen nach `plugins/plugin-manager` übernommen. Dieses Repository ist die neue kanonische Quelle. Das alte lokale Repository bleibt als Sicherung erhalten und wird nicht parallel weitergepflegt. Seine Git-Historie und persönlichen IDE-Einstellungen wurden nicht kopiert.

Die technische Plugin-Identität hat sich zu `plugin-manager` geändert. Bestehende Installationen werden dadurch nicht automatisch umbenannt. Installiere den neuen Eintrag und deaktiviere anschließend die alte Kopie. Die bisherige Bestätigung des alten Imports ist kein Abnahmetest dieses Marketplaces.

## Test mit zwei Plugins

1. Zuerst den neuen Stand von `draftm0de/ai.plugin.interview-coach` veröffentlichen.
2. Danach die Katalogänderung in diesem Repository veröffentlichen.
3. **Draftmode AI Plugins** in Claude bzw. Codex synchronisieren.
4. Prüfen, dass **Plugin Manager** und **Interview Coach** angeboten werden, und den Coach installieren.

Der Coach besitzt keinen eigenen Marketplace. Sein Repository wird über den Default-Branch ohne Tag oder Versionsbindung referenziert. Der Zugriff auf beide Repositories muss möglich sein. Der gemeinsame lokale Entwicklungs-Marketplace und die Harmonisierung des Plugin Managers folgen erst nach diesem Importtest; die bisherigen lokalen Make-Befehle betreffen weiterhin nur den Manager.
