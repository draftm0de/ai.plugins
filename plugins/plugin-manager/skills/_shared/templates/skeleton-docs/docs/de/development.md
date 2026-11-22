# Entwicklung

**Deutsch** | [English](../en/development.md)

[Start](../../README.md) · [Übersicht](README.md) · [Installation](installation.md) · [Nutzung](usage.md) · [Screens](screens.md) · [FAQ](faq.md)

## Kanonische Quelle

<!-- Plugin-Identität kommt aus plugin.json; sync-plugin erzeugt nur Host-Plugin-Manifeste. Separate Marketplaces besitzen die Kataloge. Skills liegen unter skills/. Keine Manifest-Versionen. -->

<!-- Git und Python 3.10+ sind für die Verwaltungswerkzeuge erforderlich; Make ist nur ein Komfortzugang. Für die Verwaltung wird die Host-CLI nur bei automatischer lokaler Installation/Aktualisierung benötigt; ausdrücklich gestartete Modelltests benötigen ebenfalls eine authentifizierte CLI. Publish verwendet einen ausreichend leistungsfähigen GitHub-Connector oder alternativ authentifiziertes gh; keine GitLab-MRs. Vorher Remote-Lesen, Push, PR-Erstellung/-Lesen, Checks, Regeln und kontrolliertes Mergen samt Rechten prüfen. Fehlende Fähigkeiten konkret melden, keine Werkzeuge automatisch installieren. Keine zusätzlichen Python-Pakete, Release-Actions oder Versions-/Tag-Pflichten. See ../prerequisites.md in generated projects. -->

Lies [SCOPE.md](../../SCOPE.md), [AGENTS.md](../../AGENTS.md) und [Architektur](../architecture.md). Laufzeit gehört unter skills/; scripts/ im Stamm enthält Entwicklungswerkzeuge.

## Prüfungen

<!-- Evaluate effective .local/marketplace.json ignore rules with Git before writing mappings; conflicting negations abort without changing existing files. -->

make verify prüft die Struktur; make verify REVIEW=1 sammelt Belege für den Source-Review. make test führt die konfigurierten deterministischen Tests als separaten Entwicklungsschritt aus. Durch die Skeleton-Erstellung allein wurden diese Befehle nicht ausgeführt.

## Paketierung

<!-- Explain Makefile install-local TARGET=claude|codex, separate <marketplace-name>-dev snapshots under dist/local-development, uncommitted edits, DRY_RUN=1 creating snapshots without host calls, CLI prerequisites and local-vs-account scope. Keep matching numbered/code-block formatting across hosts and languages. Explain check-plugin/sync-plugin. No plugin ZIP builder or remote install/update targets. Never recommend copying into host caches. -->

<!-- Lokale Snapshots lesen den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR ist für lokale Tests erforderlich. Es bleibt bei einem gemeinsamen `<marketplace-id>-dev`, ohne zusätzliche Marketplaces pro Branch. `configure` ist der reguläre Einrichtungsweg. `local-marketplace.example.json` ist eine optionale manuelle Kopiervorlage. Nur `.local/marketplace.json` wird zur Laufzeit für lokale Zuordnungen gelesen; diese Zuordnungen werden nicht committed. -->

make sync-plugin leitet Host-Metadaten ab; make check-plugin prüft Abweichungen. Das Plugin besitzt keine Marketplace-Kataloge.

## CI und Releases

<!-- CI validates only. Publish: reviewed diff/message, approval, commit, push, PR, checks/reviews, merge. Separate plugin and marketplace plans; publish new plugin sources first. PRs require an observed base commit. An empty remote/unborn HEAD requires separately approved initial commit and direct push, never automatic initialization. No tags or releases. -->

Die vorbereitete CI führt make test und make check-plugin aus. Ihre Existenz belegt keinen erfolgreichen Lauf. Die Erstellung führt weder Commit noch Push oder Veröffentlichung aus.

## Dokumentation pflegen

Die gewählten Dokumentationssprachen anhand bestätigter Anforderungen und tatsächlicher Source pflegen. Skeleton-Aussagen erst mit passenden Belegen ersetzen.

---

Dokumentation erstellt mit Plugin Manager. Die Urheberschaft des beschriebenen Produkts bleibt unverändert.

Testbereiche: `make test` (Unit-, Integrations- und Vertragstests), `make test-unit`, `make test-integration`, `make test-contracts`; ausdrücklich `make test-native` / `make test-behavior`. Fehlende Suiten melden `NOT RUN`. Siehe `tests/README.md`.
