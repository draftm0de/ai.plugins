# Faq

**Deutsch** | [English](../en/faq.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Produkt und Zugang

Der Manager bündelt plugin-manager, marketplace-create, configure, update, verify und publish. Der Import aus seinem GitHub-Repository wurde vom Nutzer für Claude und GPT bestätigt.

## Voraussetzungen

Git und Python 3.10+ sind für die Verwaltungswerkzeuge erforderlich; Make ist nur ein Komfortzugang. Für die Verwaltung wird die Host-CLI nur bei automatischer lokaler Installation/Aktualisierung benötigt; ausdrücklich gestartete Modelltests benötigen ebenfalls eine authentifizierte CLI. Publish verwendet einen ausreichend leistungsfähigen GitHub-Connector oder alternativ authentifiziertes gh; keine GitLab-MRs. Vorher Remote-Lesen, Push, PR-Erstellung/-Lesen, Checks, Regeln und kontrolliertes Mergen samt Rechten prüfen. Fehlende Fähigkeiten konkret melden, keine Werkzeuge automatisch installieren. Keine zusätzlichen Python-Pakete, Release-Actions oder Versions-/Tag-Pflichten.

## Datenschutz und Speicherung

Keine privaten CVs, Zustände, Zugangsdaten oder fremden Arbeitsdateien in Dokumentation übernehmen. Journals gehören außerhalb des Plugins und Quellrepositories.

## Fehlerbehebung

**`/plugin …` öffnet nur die Einstellungen?** Im Claude-Desktop-Code-Reiter wurde genau dieses Verhalten beobachtet. Verwende dort den [grafischen Installationsweg](installation.md). Die Terminal-Slash-Befehle sind nicht gleichbedeutend mit einer ausgeführten Desktop-Installation.

Bei Metadaten-Drift `make sync-plugin` ausführen und den Diff prüfen. Bei fehlendem Update den Marketplace aktualisieren und einen neuen Chat öffnen. Eine interne Codex-Anzeige 1.0.0 bedeutet nicht, dass du eine Release-Version pflegen musst.

## Grenzen der Prüfung

Strukturprüfung und erfolgreicher Import beweisen nicht alle Funktionen, automatische Updates oder einen erfolgreichen Publish-Durchlauf. ZIP und Tags sind für diesen Installationsweg nicht nötig.
