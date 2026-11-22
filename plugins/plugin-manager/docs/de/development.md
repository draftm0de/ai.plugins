# Development

**Deutsch** | [English](../en/development.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Kanonische Quelle

Die sechs öffentlichen Einstiegspunkte liegen unter `skills/<aktionsname>/SKILL.md`. Gemeinsame Regeln liegen in `skills/_shared/WORKFLOWS.md`, Helfer in `skills/_shared/scripts/` und Vorlagen in `skills/_shared/templates/`. `_shared` hat keine SKILL.md und wird nicht als zusätzlicher Skill angeboten. `docs/documentation.json` verweist auf `skills/update` und führt die gemeinsamen Quellen sowie übrigen Skills unter `extra_sources` auf.

`skills/` ist die hostneutrale Quelle. `plugin.json` steuert Plugin-Metadaten, `marketplace.json` im separaten Marketplace steuert die Kataloge. Nur der bestehende Manager in `ai.plugins/plugins/plugin-manager` bleibt eingebettet. Neue Marketplaces benötigen keinen Manager-Checkout. Kanonische Vorlagen stehen unter `skills/_shared/templates/plugin/` und `templates/marketplace/`, jeweils geteilt in `sync/` (gesynct, gehasht) und `seed/` (einmal angelegt). `make build-skeleton-hashes` schreibt die Hash-Dateien `skills/_shared/manifests/<art>.sync.json`; `make check-skeleton-hashes` prüft sie und läuft in der CI mit Exit 1 bei Abweichung.

Git und Python 3.10+ sind für die Verwaltungswerkzeuge erforderlich; Make ist nur ein Komfortzugang. Für die Verwaltung wird die Host-CLI nur bei automatischer lokaler Installation/Aktualisierung benötigt; ausdrücklich gestartete Modelltests benötigen ebenfalls eine authentifizierte CLI. Publish verwendet einen ausreichend leistungsfähigen GitHub-Connector oder alternativ authentifiziertes gh; keine GitLab-MRs. Vorher Remote-Lesen, Push, PR-Erstellung/-Lesen, Checks, Regeln und kontrolliertes Mergen samt Rechten prüfen. Fehlende Fähigkeiten konkret melden, keine Werkzeuge automatisch installieren. Keine zusätzlichen Python-Pakete, Release-Actions oder Versions-/Tag-Pflichten.

[Kanonische Voraussetzungen](../../skills/_shared/references/prerequisites.md)

## Prüfungen

Die gemeinsame [Teststruktur](../../tests/README.md) ordnet zuerst nach Testart: `unit/`, `integration/`, `contracts/`, optional `behavior/` und `native/`. Skills oder Komponenten werden darunter eingeordnet; Daten und Helfer stehen unter `fixtures/` beziehungsweise `support/`.

`make test` führt nur Unit-, Integrations- und Vertragstests aus. Einzelbereiche: `make test-unit`, `make test-integration`, `make test-contracts`. `make test-native` und `make test-behavior` werden separat angefordert. Nicht vorhandene Suiten melden ausdrücklich `NOT RUN`; alte Native-Flags erweitern den normalen Testlauf nicht.

`make test` prüft Werkzeuge und temporäre Repository-Abläufe. `make verify` und `make verify SOURCE=...` lesen nur Struktur und verfügbare lokale Zuordnungen. Sie führen keine Zielskripte oder Reparaturen aus. `make validate-docs OUTPUT=.` prüft Dokumentation gesondert.

Native Abnahme: `make test-native` im Manager-Ordner. Der Workflow-Test verwendet fiktive temporäre Repositories und isolierte Claude-/Codex-Profile. Er installiert zwei separate Plugins und prüft die geladenen Inhalte nach uncommitteten Änderungen. Dies ersetzt keine GitHub-/GUI-Abnahme.

## Paketierung

Repository-Installation benötigt keine Plugin-ZIPs oder Manifest-Versionen. `make sync-plugin`/`check-plugin` betreffen Plugin-Manifeste; `make sync-marketplace`/`check-marketplace` betreffen Host-Kataloge. Die Root-Aufrufe `sync-plugin`/`check-plugin` in ai.plugins berücksichtigen zusätzlich den eingebetteten Manager.

`make install-local TARGET=claude` beziehungsweise `TARGET=codex` erstellt gefilterte Snapshots unter `dist/local-development/` und installiert alle zugeordneten Plugins als `<marketplace-id>-dev`. Der Aufruf braucht weder Commit noch Push, und ein erneuter Aufruf erneuert die Snapshots. `DRY_RUN=1` schreibt Snapshots ohne Host-Aufruf. Persönliche Host-Caches werden nicht direkt verändert. Die CLI verwaltet ihre eigenen Installationen.

Lokale Pfade stehen Git-ignoriert in `.local/marketplace.json`: im Marketplace unter `sources`, im Plugin unter `marketplace` und `marketplaces`. Ein explizites `MARKETPLACE=...` überschreibt den Standard für den Aufruf. Alle benötigten Checkouts müssen vor Installation verfügbar sein.

Lokale Snapshots lesen den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR ist für lokale Tests erforderlich. Es bleibt bei einem gemeinsamen `<marketplace-id>-dev`, ohne zusätzliche Marketplaces pro Branch.

Die lokale Zuordnung eines Plugins zu seinem einen Marketplace richtet `plugin-manager` (associate) ein und ändert sie. Der Pfad des Marketplace-Checkouts steht in der von Git ignorierten `.project/plugins/plugin-manager/local.json` des Plugins; die Checkouts der Plugins stehen unter `sources` in der von Git ignorierten `.local/marketplace.json` des Marketplace; diese Zuordnungen werden nicht committet. `local-marketplace.example.json` ist eine optionale manuelle Kopiervorlage für die Marketplace-Seite.

Ohne Make im Marketplace:

```sh
python3 -B scripts/local_plugins.py install-local --target claude
```

## CI und Releases

CI prüft Tests, Metadaten und Dokumentation und veröffentlicht nichts. [Publish](publish.md) verwendet getrennte Pläne je Repository. Neue Plugin-Quellen müssen veröffentlicht und beobachtet sein, bevor der Marketplace-Eintrag veröffentlicht wird. Keine Release-Actions, Tags oder Plugin-ZIPs. [Prüfstand](release-evidence.md).

## Dokumentation pflegen

Die Aktion update liest aktuelle Quellen und pflegt die gespeicherte Sprachauswahl. plugin-create erzeugt Vorlagen; der Agent vervollständigt diese anhand belegter Produktfunktionen. Kein erfundener Herausgeber, keine erfundene Lizenz und keine erfundenen Skill-Inhalte. init wird nicht unterstützt.

[Create-/Configure-Aufrufe](../../skills/_shared/references/workflows.md)

Für ein Update: „Führe update für dieses Repository aus und prüfe anschließend.“ Der Agent liest `docs/documentation.json`, Skill, Referenzen, Manifeste und Werkzeuge neu und pflegt `README.md`, `README.en.md` sowie `docs/de/` und `docs/en/`. Scaffold erzeugt nur fehlende Dateien; vorhandene Inhalte werden gezielt überarbeitet. `make validate-docs OUTPUT=.` prüft Struktur und lokale Links. Diese Prüfungen ersetzen keinen inhaltlichen Abgleich oder Host-Test.

Neue Plugin- und Marketplace-Vorlagen enthalten SCOPE.md sowie gemeinsame Entwicklungsregeln in AGENTS.md und docs/architecture.md; CLAUDE.md verweist darauf. Diese Dateien sind versionierte Soll-/Strukturvorgaben. Bestehende Inhalte bleiben erhalten; fachliche Anforderungen werden nicht aus dem Code erfunden. Die Review-Regressionsfälle unter `tests/integration/verify/test_scope_review.py` prüfen Beleggrenzen, fehlende Anforderungen, Skeletons und falsche Runtime-Abhängigkeiten ohne Zielcode-Ausführung. Sie beweisen keine Zuverlässigkeit eines LLM-Reviews.

### Modelltests für den Zielbild-/Source-Review

Im Manager-Verzeichnis ausdrücklich `make test-behavior CLI=claude` oder `CLI=codex` ausführen; `CASE=correct_consent` wählt einen Fall. [Szenarien, Auswertung und Grenzen](../../tests/behavior/README.md). Beide Modelle erhalten fiktive vollständige Dateien und dieselben Review-Regeln ohne erwartete Ergebnisse. Korrekte Implementierungen, echte Fehler, Testlücken, fehlende Source und eingeschleuste Erfolgsmeldungen werden geprüft. Die automatische Auswertung wird durch manuelle Sichtung ergänzt. Keine Modellaufrufe im normalen Testlauf; keine Installation oder Veröffentlichung.

Formatprüfung vor Änderungen: Keine parallelen Host-Skill-Verzeichnisse und kein marketplace-Schlüssel in der Distribution. Unbekannte Katalogeintragsfelder werden vor associate abgelehnt, nicht verworfen. Dokumentations-Schema-Versionen müssen ganzzahlig sein. Abweichende vorhandene docs/architecture.md oder docs/prerequisites.md blockieren plugin-create, ohne Inhalte zu überschreiben.

Auch plugin-create prüft alte Host-Verzeichnisse vor Änderungen. Skill-Import über plugin-create ist nicht unterstützt; Layout- und Dokumentationsmanifest-Prüfungen bleiben bestehen.
