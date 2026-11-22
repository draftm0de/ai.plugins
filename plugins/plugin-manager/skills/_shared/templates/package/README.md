# Plugin Manager

**Deutsch** | [English](README.en.md)

Dieses Plugin dokumentiert zugängliche lokale Skills und Plugins anhand ihrer Quellen. Die Dokumentationssprachen werden pro Repository festgelegt: nur Deutsch, nur Englisch oder beide. Nutze `plugin-manager`, um einen Marketplace einzurichten oder ein separates Plugin zu erstellen, `configure` für dessen Zuordnung, `update` zur Erneuerung der Dokumentation oder `verify` zur lesenden Strukturprüfung. Der Agent fragt bei wesentlichen Unklarheiten nach. Eine erfolgreiche Strukturprüfung bestätigt noch keine Produktionsreife. Das Plugin veröffentlicht und installiert nichts ohne Auftrag.

In Claude: `/plugin-manager:verify QUELLPFAD`, entsprechend `/plugin-manager:plugin-manager` (Einrichtung, Plugin oder Marketplace) oder `:update`. In ChatGPT fordere die Aktion in natürlicher Sprache an. Die Quelle muss dem Host zugänglich sein; die Helfer benötigen Python 3.10 oder neuer.

[Workflow und Grenzen](skills/_shared/WORKFLOWS.md)

## Veröffentlichen mit Freigabe

`/plugin-manager:publish QUELLPFAD` bereitet Diff, Commit-Nachricht und PR vor. Nach Freigabe folgen Feature-Branch, Commit, Push, PR, Prüfungen und Merge. Keine Versionen, Tags oder Releases. Neue Plugin-Repositories vor ihren Marketplace-Einträgen veröffentlichen. Der Journalhelfer veröffentlicht selbst nichts. [Workflow](skills/_shared/references/publish.md).

PRs benötigen einen belegten bestehenden Basisbranch. Für ein leeres Remote ohne lokalen HEAD ist ein eigener Plan mit ausdrücklicher Freigabe für ersten Commit und direkten Push ohne PR erforderlich. Es gibt keine automatischen Initial-Commits. Schema-4-Journale binden auch Änderungen, Hinzufügen und Entfernen des Codex-Manifests außerhalb der Dateiauswahl.

Git und Python 3.10+ sind für die Verwaltungswerkzeuge erforderlich; Make ist nur ein Komfortzugang. Für die Verwaltung wird die Host-CLI nur bei automatischer lokaler Installation/Aktualisierung benötigt; ausdrücklich gestartete Modelltests benötigen ebenfalls eine authentifizierte CLI. Publish verwendet einen ausreichend leistungsfähigen GitHub-Connector oder alternativ authentifiziertes gh; keine GitLab-MRs. Vorher Remote-Lesen, Push, PR-Erstellung/-Lesen, Checks, Regeln und kontrolliertes Mergen samt Rechten prüfen. Fehlende Fähigkeiten konkret melden, keine Werkzeuge automatisch installieren. Keine zusätzlichen Python-Pakete, Release-Actions oder Versions-/Tag-Pflichten.

Lokale Snapshots lesen den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR ist für lokale Tests erforderlich. Es bleibt bei einem gemeinsamen `<marketplace-id>-dev`, ohne zusätzliche Marketplaces pro Branch.

Die lokale Zuordnung eines Plugins zu seinem einen Marketplace richtet `plugin-manager` (associate) ein und ändert sie. Der Pfad des Marketplace-Checkouts steht in der von Git ignorierten `.project/plugins/plugin-manager/local.json` des Plugins; die Checkouts der Plugins stehen unter `sources` in der von Git ignorierten `.local/marketplace.json` des Marketplace; diese Zuordnungen werden nicht committet. `local-marketplace.example.json` ist eine optionale manuelle Kopiervorlage für die Marketplace-Seite.

## Skills

`plugin-manager`, `verify`, `update` und `publish`; die Marketplace-Zuordnung eines Plugins ist ein Flow von plugin-manager. Gemeinsame Regeln: `skills/_shared/WORKFLOWS.md`; plugin-manager ist der zentrale Einstieg.
