# Usage

**Deutsch** | [English](../en/usage.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Einrichten

Gib einen zugänglichen Quellordner an. Sprache und Zielordner werden pro Repository geklärt; `docs/documentation.json` speichert nur Quellenzeiger, Sprache und Exportkonfiguration. Ohne lokalen Dateizugriff muss eine bereinigte Quellkopie bereitgestellt werden.

## Ablauf auswählen

Wähle init, update, plugin-verify, marketplace-verify, verify, export oder publish. In Claude Code beispielsweise `/plugin-manager:init QUELLE ZIEL`. In Codex/GPT wählst du die passende Fähigkeit oder beschreibst die Aktion. Die Claude-Slash-Oberfläche wird nicht für jeden Host vorausgesetzt.

## Ausgabe verstehen

Init erzeugt eine separate Kopie unter `skills/`, ein versionsloses Manifest, beide Marketplace-Dateien, das Claude-Manifest und Entwicklungs-/Dokumentationsvorlagen. Fehlende Repository-URL und Herausgeberangaben müssen geklärt werden. Vorlagen allein sind noch keine fertige Produktdokumentation. Verify meldet `valid`, den erkannten Repository-Typ, den geprüften Pfad und Grenzen der Prüfung. Ein strukturell gültiger Aufbau ist keine Host-Abnahme.

## Sitzung steuern

Beschränke den Auftrag auf gewünschte Dateien oder Aktionen. Init überschreibt keine bestehenden Projekte. Bei vorhandenen Projekten werden Änderungen gezielt vorgenommen; prüfe anschließend den Diff. Ein Abbruch macht bereits erfolgte Änderungen nicht automatisch rückgängig.

## Später fortsetzen

Update liest aktuelle Quellen erneut. Publish kann mit einem privaten Journal fortgesetzt werden, nachdem tatsächlicher GitHub-Stand und ursprüngliche Freigabe überprüft wurden. Alte Release-Journals benötigen einen neuen Plan.

## Spezialisierte Abläufe

[Publish](publish.md) schlägt die Commit-Nachricht vor und führt nur nach Freigabe Commit → Push → PR → Prüfungen → Merge aus. Keine Versionsfreigabe, Tags oder Releases. Export baut dagegen ein ZIP für die Website aus vorhandenem Markdown; dieses ZIP ist kein Installationspaket.

### Bestehendes Projekt prüfen

`/plugin-manager:plugin-verify PFAD` prüft ein Plugin, `/plugin-manager:marketplace-verify PFAD` einen Marketplace. `/plugin-manager:verify PFAD` erkennt den Typ. Der Zielpfad kommt aus deinem geöffneten Projekt oder deiner ausdrücklichen Angabe. Der Installationsordner des Managers ist nicht automatisch das Ziel. Bei falschem Typ oder uneindeutigem Ordner wird nichts geändert. In Codex die entsprechende Fähigkeit auswählen oder die Prüfung in natürlicher Sprache anfordern.

`configure` würde Zuordnungen und Metadaten schreiben; Verify liest nur. Configure sowie getrennte Create-Aktionen sind noch nicht umgesetzt.
