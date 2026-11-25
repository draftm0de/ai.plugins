# Skills

**Deutsch** | [English](../en/skills.md)

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Start](../../README.md) · [Installation](installation.md) · [Skills](skills.md) · [Begriffe](concepts.md)

Fünf Skills, je einer pro Aufgabe. In Claude Code rufst du sie mit `/plugin-manager:<skill>` auf.

## Überblick

| Skill | Wofür |
| --- | --- |
| [docs](#docs) | Dokumentation aus den Quellen schreiben |
| [modify](#modify) | Name, Anzeigename, Beschreibung ändern |
| [publish](#publish) | Kontrolliert veröffentlichen |
| [setup](#setup) | Einrichten und aktuell halten |
| [verify](#verify) | Nur lesend prüfen |

## docs

### Beschreibung

Schreibt oder aktualisiert die Dokumentation eines Plugins oder Marketplace in den gewählten Sprachen, aus `SCOPE.md`, den Skills und dem Quellcode.

### Ablauf

1. Prüft, ob das Repository eingerichtet ist.
2. Liest die Quellen und klärt Offenes mit dir.
3. Schreibt README, Installation, Skills beziehungsweise Plugin-Liste und Begriffe.
4. Prüft Struktur und Links.

### Beispiel

`/plugin-manager:docs` nach einem neuen Skill: Die Skills-Seite bekommt seinen Abschnitt.

### Liest und schreibt

Liest die Quellen des Repositorys. Schreibt README und Seiten unter `docs/`, vorhandene eigene Texte bleiben.


## modify

### Beschreibung

Ändert, was ein Repository über sich sagt: technischen Namen, Anzeigenamen und Beschreibung.

### Ablauf

1. Prüft, ob das Repository eingerichtet ist.
2. Fragt, was sich ändern soll.
3. Zeigt alle betroffenen Dateien, ohne zu schreiben.
4. Schreibt erst nach deinem Ja.

### Beispiel

„Gib dem Plugin den Anzeigenamen Bewerbungs-Coach.“

### Liest und schreibt

Liest die Konfiguration und den zugehörigen Marketplace. Schreibt die Manifeste und, beim Plugin, den Marketplace-Eintrag.


## publish

### Beschreibung

Bereitet eine Veröffentlichung vor und führt sie nur mit deiner Freigabe aus, über einen geprüften Pull Request.

### Ablauf

1. Prüft, ob das Repository eingerichtet ist.
2. Zeigt den Diff, die Commit-Nachricht und die Prüfungen.
3. Wartet auf deine Freigabe.
4. Erstellt Branch, Commit, Push und Pull Request.

### Beispiel

„Bereite die Änderungen an der Dokumentation zur Veröffentlichung vor.“

### Liest und schreibt

Liest den Diff und die Git-Angaben. Schreibt erst nach der Freigabe in Git und GitHub; sein Protokoll liegt außerhalb des Repositorys.


## setup

### Beschreibung

Bringt ein Plugin- oder Marketplace-Repository in den eingerichteten Zustand und hält die gemeinsamen Dateien aktuell. Beliebig oft aufrufbar.

### Ablauf

1. Sprache klären.
2. Plugin oder Marketplace konfigurieren.
3. Gemeinsame Dateien anlegen und aktualisieren; unveränderte Kopien ohne Frage, geänderte nur nach deiner Entscheidung.
4. Eine Zeile „vollständig konfiguriert“.

### Beispiel

`/plugin-manager:setup` in einem leeren, geklonten Repository.

### Liest und schreibt

Liest den Ordner und den ausgewählten Marketplace. Schreibt Verwaltungsdateien unter `.project/`, die gemeinsamen Dateien und beim Anlegen das Plugin-Gerüst.


## verify

### Beschreibung

Meldet, ob ein Repository den Regeln entspricht, und was noch nicht belegt ist.

### Ablauf

1. Erkennt selbst, ob Plugin oder Marketplace.
2. Prüft Struktur und Standards.
3. Auf Wunsch vergleicht es `SCOPE.md` mit dem Quellcode.

### Beispiel

`/plugin-manager:verify` vor einer Veröffentlichung.

### Liest und schreibt

Liest das Repository. Schreibt nichts und führt keinen Code des Repositorys aus.

---

Dokumentation mit Plugin Manager erstellt.
