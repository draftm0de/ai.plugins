# Plugin Manager

**Deutsch** | [English](README.en.md)

<img src="docs/assets/zyris-icon.png" alt="ZYRIS" width="48">

## Für wen ist das gedacht?

Für Entwickler und Teams, die Skills als installierbare Plugins pflegen. Der Manager unterstützt Struktur, Dokumentation, Prüfung und die Veröffentlichung über einen geprüften GitHub-PR.

## So sieht es aus

[Beispiele und vorhandene Claude-Dialoge](docs/de/screens.md) zeigen die Nutzung. Frühere Importbestätigungen sind keine Abnahme der neuen Create-/Configure-Abläufe.

## Funktionen und Modi

**marketplace-create** richtet einen geklonten Marketplace ein. **plugin-create** erstellt ein separates Plugin und ordnet es zu. **configure** verbindet ein bestehendes Plugin mit einem Marketplace. **plugin-verify**, **marketplace-verify** und **verify** prüfen ausschließlich lesend. **update** pflegt Dokumentation und **publish** bereitet getrennte, freigabepflichtige Veröffentlichungen vor. `init` wird nicht unterstützt. [Abläufe](docs/de/usage.md).

Die sechs Skills heißen `marketplace-create`, `plugin-create`, `configure`, `verify`, `update` und `publish`. `plugin-manager` bezeichnet nur das Plugin. Gemeinsame Regeln und Werkzeuge liegen in [`skills/_shared/`](skills/_shared/WORKFLOWS.md), ohne zusätzlichen Skill. Explizite Prüfvarianten bleiben Befehle; init wird nicht unterstützt.

## Schnellstart

Füge `https://github.com/draftm0de/ai.plugins` in der Plugin-Verwaltung als Marketplace hinzu und installiere **Plugin Manager**. Kein ZIP und kein Tag nötig. [Installationswege](docs/de/installation.md).

## Nutzung

Wähle das Plugin und sage: „Prüfe dieses Repository mit verify.“ Für Dokumentation: „Aktualisiere die Dokumentation auf Deutsch und Englisch.“ In Claude Code sind auch `/plugin-manager:verify PFAD` und die weiteren Aktionskommandos verfügbar. [Nutzung](docs/de/usage.md).

`update` ist der Skill-Einstieg für die Aktion **update**. Er aktualisiert gepflegtes Markdown anhand aktueller Quellen und Vorlagen; README wird nicht bei jedem Build automatisch erzeugt. [Dokumentation pflegen](docs/de/development.md#dokumentation-pflegen).

## Speicherung und Datenschutz

Der Manager schreibt Dokumentationsdateien und bei plugin-create eine separate Quellkopie. Publish-Journals liegen außerhalb von Quelle und Plugin-Installation. Private Daten, Zugangsdaten und fremde Änderungen werden nicht übernommen. Der KI-Host verarbeitet die bereitgestellten Quellen nach seinen Bedingungen.

## Projektstatus

Laut Nutzer sind Manager und Coach im veröffentlichten Marketplace vorhanden. Die früher bestätigten Claude-/GPT-Importe betreffen den damaligen Stand; die aktuellen Manager-Erweiterungen liegen noch lokal vor. Isolierte CLI-Tests sind separat dokumentiert. Das bestätigt weder sämtliche Funktionen noch automatische Updates oder den vollständigen Publish-Ablauf. Lizenz: [MIT](LICENSE). [Prüfstand](docs/de/release-evidence.md).

## Entwicklung

`plugin-create --skeleton` startet ohne Fachinhalt; `--source` übernimmt einen bestehenden Skill. Das Skeleton enthält eine noch zu bestätigende `SCOPE.md` und Entwicklungsregeln. `verify` bietet einen ausdrücklich gewählten lesenden Zielbild-/Source-Review: statische Belegprüfung mit `REVIEW=1`, danach fachlicher Vergleich durch den Agenten. Keine automatische Reparatur oder Testausführung. [Ablauf und Grenzen](docs/de/usage.md).

Die [Testübersicht](tests/README.md) beschreibt die gemeinsame Struktur nach Testart. `make test` prüft Unit-, Integrations- und Vertragstests; native Host- und Modelltests werden separat gestartet.

```sh
make sync-plugin
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

`make sync-plugin` erzeugt die einzucheckenden Host-Metadaten. `make install-local` und `make update-local` testen lokale Änderungen ohne Commit oder Push; die Skill-Aktion **update** pflegt dagegen Dokumentation. [Entwicklung](docs/de/development.md).

Dokumentation erstellt mit Plugin Manager.
