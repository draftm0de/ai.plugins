# Plugin Manager

**Deutsch** | [English](README.en.md)

<img src="assets/icon.png" alt="draftmode.io" width="48">

## Für wen ist das gedacht?

Für Entwickler und Teams, die Skills als installierbare Plugins pflegen. Der Manager unterstützt Struktur, Dokumentation, Prüfung und die Veröffentlichung über einen geprüften GitHub-PR.

## So sieht es aus

[Beispiele und vorhandene Claude-Dialoge](docs/de/screens.md) zeigen die Nutzung. Frühere Importbestätigungen sind keine Abnahme der neuen Create-/Configure-Abläufe.

## Funktionen und Modi

**setup** (`/plugin-manager:setup`) richtet einen geklonten Marketplace ein oder erstellt ein separates Plugin und ordnet es zu, als geführte Abläufe; der Skill prüft den Zustand, führt genau den nötigen Flow aus und darf wiederholt aufgerufen werden. Die Marketplace-Zuordnung eines Plugins (genau ein Marketplace) ändert er auf Anfrage im Flow `associate`. **verify** prüft ausschließlich lesend und erkennt selbst, ob ein Plugin oder ein Marketplace vorliegt. **docs** pflegt Dokumentation, **modify** ändert Namen, Anzeigenamen und Beschreibung eines Plugins oder Marketplace (erst Folgen zeigen, dann nach deinem Ja schreiben) und **publish** bereitet getrennte, freigabepflichtige Veröffentlichungen vor; alle drei starten nur, wenn das Arbeitspaket bereit ist, sonst verweisen sie auf `setup`. `init` wird nicht unterstützt. [Abläufe](docs/de/usage.md).

Die fünf Skills heißen `setup`, `docs`, `modify`, `verify` und `publish`. Gemeinsame Regeln und Werkzeuge liegen in [`skills/_shared/`](skills/_shared/WORKFLOWS.md). Die Art (Plugin oder Marketplace) ist nie ein Aufrufargument; init wird nicht unterstützt.

## Schnellstart

Füge `https://github.com/draftm0de/ai.plugins` in der Plugin-Verwaltung als Marketplace hinzu und installiere **Plugin Manager**. Kein ZIP und kein Tag nötig. [Installationswege](docs/de/installation.md).

## Nutzung

Wähle das Plugin und sage: „Prüfe dieses Repository mit verify.“ Für Dokumentation: „Aktualisiere die Dokumentation auf Deutsch und Englisch.“ In Claude Code sind auch `/plugin-manager:verify PFAD` und die weiteren Aktionskommandos verfügbar. [Nutzung](docs/de/usage.md).

`docs` ist der Skill-Einstieg für die Aktion **docs** (`/plugin-manager:docs`). Er aktualisiert gepflegtes Markdown anhand aktueller Quellen und Vorlagen; README wird nicht bei jedem Build automatisch erzeugt. [Dokumentation pflegen](docs/de/development.md#dokumentation-pflegen).

## Speicherung und Datenschutz

Der Manager schreibt Dokumentationsdateien und bei `create --kind plugin` ein separates Plugin-Gerüst. Publish-Journals liegen außerhalb von Quelle und Plugin-Installation. Private Daten, Zugangsdaten und fremde Änderungen werden nicht übernommen. Der KI-Host verarbeitet die bereitgestellten Quellen nach seinen Bedingungen.

## Projektstatus

Laut Nutzer sind Manager und Coach im veröffentlichten Marketplace vorhanden. Die aktuellen Manager-Erweiterungen liegen noch lokal vor. Das bestätigt weder sämtliche Funktionen noch automatische Updates oder den vollständigen Publish-Ablauf. Lizenz: [MIT](LICENSE).

## Entwicklung

`create --kind plugin --skeleton` erstellt ausschließlich ein neues Gerüst ohne Fachinhalt. Ein Skill-Import wird nicht angeboten. Das Skeleton enthält eine noch zu bestätigende `SCOPE.md` und Entwicklungsregeln. `verify` bietet einen ausdrücklich gewählten lesenden Zielbild-/Source-Review: statische Belegprüfung mit `REVIEW=1`, danach fachlicher Vergleich durch den Agenten. Keine automatische Reparatur oder Testausführung. [Ablauf und Grenzen](docs/de/usage.md).

Die [Testübersicht](tests/README.md) beschreibt die gemeinsame Struktur nach Testart. `make test` prüft Unit-, Integrations- und Vertragstests; native Host- und Modelltests werden separat gestartet.

```sh
make sync-plugin
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

`make sync-plugin` erzeugt die einzucheckenden Host-Metadaten. `make install-local` testen lokale Änderungen ohne Commit oder Push; die Skill-Aktion **docs** pflegt dagegen Dokumentation. [Entwicklung](docs/de/development.md).

Dokumentation erstellt mit Plugin Manager.
