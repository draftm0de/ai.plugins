# Usage

**Deutsch** | [English](../en/usage.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Einrichten

Zielpfade stammen aus deinem geöffneten Projekt oder einer ausdrücklichen Angabe, nie automatisch aus der Manager-Installation. Vorhandene Angaben und Git-Origin werden übernommen; nur fehlende oder widersprüchliche Angaben werden geklärt. Anzeigename und technische Kennung sind getrennte Angaben. Herausgeber, Lizenz und fachliche Skill-Inhalte werden nicht erfunden.

## Ablauf auswählen

In Claude Code: `/plugin-manager:marketplace-create`, `/plugin-manager:plugin-manager` oder `/plugin-manager:configure`. In Codex/GPT die entsprechende Fähigkeit wählen oder die Aktion beschreiben. `init` wird nicht unterstützt.

Der zentrale Einstieg `plugin-manager` liest zuerst den Projektzustand und verwendet die gespeicherte Bedienersprache; fehlt sie, fragt er ausdrücklich danach. Er synchronisiert das Skeleton und startet die geführte Erstkonfiguration nur ohne plugin.json. Dokumentationssprachen bleiben unabhängig. Offene Konfigurationsangaben verhindern Generator-Schreibzugriffe. Bestehende Plugins werden nicht neu erstellt: Nach nötiger Skeleton-Arbeit meldet der Einstieg den Zustand und wartet. Für eine Marketplace-Zuordnung eines bestehenden Plugins bleibt der separate Skill `configure` verfügbar.

Vor der Erstellung klärt der Agent die Lizenzentscheidung. Eine eindeutige vorhandene Lizenz oder bereits getroffene Entscheidung wird übernommen; andernfalls fragt er nach einer Lizenz oder einer ausdrücklichen Vertagung. Ohne Antwort beginnt die Erstellung nicht. Widersprüche werden vor Änderungen geklärt und vorhandene Lizenzdateien bleiben erhalten. Eine vertagte Entscheidung erscheint im Abschlussbericht als offen. Eine gewählte Lizenz wird umgesetzt: MIT mit bestätigtem Copyright-Jahr und Rechteinhaber, andere Lizenzen anhand einer ausdrücklich bestätigten vollständigen Textdatei. Lizenzdatei, Manifest und Dokumentation werden gemeinsam erstellt und geprüft. Die Entscheidung bleibt in docs/license.md erhalten, auch bei ausdrücklicher Vertagung.

| Aktion | Eingaben | Ergebnis |
| --- | --- | --- |
| marketplace-create | Geklontes Repository, Anzeigename, Kennung, Herausgeber | Gemeinsamer Katalog, beide Host-Kataloge und eigenständige Werkzeuge |
| plugin-manager | Separater Checkout/Pfad, bestehende GitHub-URL, Marketplace, Name, Kennung, Beschreibung, Herausgeber, Skeleton-Modus, Sprachen | Plugin-Struktur ohne eigene Kataloge, Zuordnung und Dokumentationsvorlagen |
| configure | Bestehendes Plugin und gewählter Marketplace | Katalogeintrag und lokale Zuordnung; andere Zuordnungen bleiben |

### Dokumentation aktualisieren

Nutze `update` beziehungsweise in Claude Code `/plugin-manager:update PFAD`. Die Aktion liest die aktuellen Produktquellen und die gespeicherte Sprachwahl neu, aktualisiert README und Anleitungen und prüft sie anschließend. Sie installiert nichts und veröffentlicht nichts. `install-local` ist der getrennte Befehl zum Erneuern lokaler Plugin-Snapshots.

## Ausgabe verstehen

Neue Plugins besitzen eigene Manifeste, Skills und Dokumentation, jedoch keine Marketplace-Kataloge. Der Agent vervollständigt erzeugte Dokumentationsvorlagen aus den Quellen. `valid` und `structure_valid` bewerten die veröffentlichbare Struktur. `local_development.complete` bewertet getrennt die lokale Entwicklungskonfiguration. Fehlende Checkouts oder `.local`-Dateien sind bei frischen Clones erwartbar und machen den veröffentlichten Katalog nicht ungültig. Die Prüfung führt keinen Zielcode aus.

## Sitzung steuern

Vorhandene Dateien werden zuerst geprüft. Abweichende Werkzeugdateien und widersprüchliche Zuordnungen stoppen den Ablauf zur gezielten Klärung; persönliche Daten und Installationen bleiben erhalten. Fehlende Checkouts werden nur bei plugin-create aus der angegebenen bestehenden GitHub-Quelle geklont. Configure migriert keine alten Plugin-Kataloge automatisch.

## Später fortsetzen

Update liest aktuelle Quellen erneut. Publish kann mit einem privaten Journal fortgesetzt werden, nachdem tatsächlicher GitHub-Stand und ursprüngliche Freigabe überprüft wurden. Alte Release-Journals benötigen einen neuen Plan.

## Spezialisierte Abläufe

`make install-local TARGET=claude|codex` verwenden alle zugeordneten Plugins in einem gemeinsamen `<marketplace-id>-dev`. Im Plugin überschreibt `MARKETPLACE=/pfad/zum/katalog` den lokalen Standard nur für den Aufruf. Fehlende benötigte Checkouts stoppen vor Host-Änderungen. `DRY_RUN=1` erzeugt nur Snapshots.

[Publish](publish.md) behandelt Plugin und Marketplace getrennt: bei neuen Einträgen zuerst Plugin, danach Marketplace. Branch → Commit → Push → PR → Prüfungen → Merge erfordern eine konkrete Freigabe. Keine Tags, Releases oder Plugin-ZIPs.

[Technische Aufrufe und Eingaben](../../skills/_shared/references/workflows.md)

Lokale Zuordnungen werden erst geschrieben, nachdem Git die vorgeschlagenen Ignore-Regeln als wirksam bestätigt hat. Negationen, die `.local/marketplace.json` sichtbar machen, stoppen vor Änderungen; bestehende Inhalte und Zuordnungen bleiben erhalten. [Erstveröffentlichung ohne HEAD](publish.md#erstveröffentlichung-ohne-head) erfordert eine eigene ausdrückliche Freigabe.

Lokale Snapshots lesen den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR ist für lokale Tests erforderlich. Es bleibt bei einem gemeinsamen `<marketplace-id>-dev`, ohne zusätzliche Marketplaces pro Branch.

`configure` ist der reguläre Einrichtungsweg. `local-marketplace.example.json` ist eine optionale manuelle Kopiervorlage. Nur `.local/marketplace.json` wird zur Laufzeit für lokale Zuordnungen gelesen; diese Zuordnungen werden nicht committed.

### Skeleton vor der fachlichen Implementierung

Neue Skeleton-Seiten werden in den gewählten Sprachen mit dem tatsächlichen Gerüststatus ausgefüllt und vor dem Schreiben validiert. Vorhandene Texte bleiben erhalten. Die Abschlussprüfung bewertet anschließend die tatsächliche Plugin-Struktur, den Marketplace und die Dokumentation getrennt. Fehler in erhaltenen Seiten bleiben sichtbar; `checks.status=needs_attention` bedeutet, dass die Erstellung noch offene Prüfbefunde hat. `passed` prüft auch die technische Konsistenz von Lizenzdateien und Dokumentation; das ist keine rechtliche Bewertung oder fachliche Abnahme. Der Abschlussbericht nennt außerdem die Lizenzentscheidung, tatsächliche Lizenzdateien und noch ausstehende Tests beziehungsweise Host-Prüfungen.

`plugin-create --skeleton` erstellt ein ausdrücklich unfertiges Plugin, auch wenn es noch keine fachliche Skill-Quelle gibt. Marketplace, technische Kennung, Anzeigename, vorhandenes GitHub-Repository, Herausgeber und Dokumentationssprachen werden aus bekannten Angaben übernommen oder gezielt geklärt. Die Beschreibung ist optional; ohne bestätigte Beschreibung steht ausdrücklich „unimplemented“ im Manifest. Keine fachlichen Funktionen oder Lizenz werden erfunden.

```sh
# Im ai.plugins-Checkout; Zielrepository existiert bereits lokal mit Git-Origin:
python3 -B skills/_shared/scripts/workflows.py plugin-create --root /pfad/zum/plugin --marketplace /pfad/zum/katalog --skeleton --name beispiel-plugin --display-name "Beispiel Plugin" --author "Bestätigter Herausgeber" --languages de en --default-language de --license deferred
```

Die Erstellung unterstützt ausschließlich `--skeleton`; `--source` und `--import` werden vor Änderungen abgelehnt. Das Skeleton besitzt einen nicht funktionalen Skill mit sichtbarer Markierung, Manifeste, Zuordnung, Dokumentationsgerüst, Testwerkzeuge, `SCOPE.md`, `AGENTS.md`, `CLAUDE.md` und `docs/architecture.md`. Abweichende vorhandene Anweisungen oder SCOPE-Dateien werden nicht überschrieben. Eine gültige Struktur ist keine fachliche Abnahme.

### Zielbild gegen Source prüfen

1. In `SCOPE.md` Zweck, Nicht-Ziele und beobachtbare Abnahmekriterien mit dem Nutzer bestätigen. Unbekanntes bleibt `draft`.
2. Claude/Codex implementiert innerhalb der Entwicklungsregeln. Fachliche Laufzeit gehört unter `skills/`, Entwicklungswerkzeuge unter `scripts/`; Tests folgen der gemeinsamen Teststruktur.
3. `verify` ausdrücklich um einen Zielbild-/Source-Review bitten. Der Skill liest die bestätigten Anforderungen und die tatsächliche Source-/Testlogik und berichtet pro Anforderung Beleg, Abweichung, Begründung und Änderungsvorschlag.

```sh
make verify SOURCE=/pfad/zum/plugin REVIEW=1
# Ohne Make, mit dem vertrauenswürdigen Manager-Helfer:
python3 plugins/plugin-manager/skills/_shared/scripts/verify.py --source /pfad/zum/plugin --review
```

Diese Befehle sammeln statische Belege; sie ersetzen den anschließenden fachlichen Agent-Review nicht. `ready_for_source_review` heißt „Belege verfügbar“, nicht „Anforderung erfüllt“. `needs_attention` liefert konkrete Befunde und Exitcode 1, ohne dadurch `structure_valid` umzudeuten. Alle Anforderungen bleiben im automatischen Bericht fachlich `unverified`; Tests werden nicht ausgeführt. Der Agent unterscheidet anschließend `supported_by_source`, `contradicted`, `missing_evidence` und `not_assessed` mit tatsächlichen Datei-/Zeilenbelegen. Auch Source-Unterstützung ist kein Laufzeit- oder Host-Nachweis.

SCOPE verwendet stabile Überschriften wie `## R1: Zustimmung vor Speicherung` und je Anforderung `Status: confirmed`, ein `Acceptance:`-Kriterium sowie einzelne `Source:`- und `Test:`-Dateiverweise. Der Gesamtstatus steht vor den Anforderungen. Belegverweise dürfen nur öffentliche Source-/Testdateien benennen; private Daten, Fixtures und Symlinks werden nicht als Review-Belege gelesen. [Review-Regeln](../../skills/_shared/references/scope-review.md).

Verify repariert nichts, startet keine Tests und verändert das Zielbild nicht. Ein Bericht erscheint standardmäßig im Gespräch; Speicherung braucht einen ausdrücklich gewählten Zielpfad. Agent-Anweisungen helfen bei der Einhaltung der Struktur, garantieren aber kein LLM-Verhalten. Tests und fachlicher Review ergänzen sie.

## Projekt-Einrichtung (zentraler Einstieg)

Der Skill `plugin-manager` (Command-Datei `commands/plugin-manager.md`; in Claude Code üblicherweise `/plugin-manager:plugin-manager`, nicht im Host getestet) bereitet ein ausdrücklich gewähltes eigenständiges Plugin-Repository vor: Bedienersprache und gemeinsame Entwicklungsdateien prüfen, Fehlendes ergänzen, Ownership festhalten. Marketplaces und der eingebettete Manager sind keine Ziele.

```sh
python3 -B skills/_shared/scripts/project_setup.py status --target <plugin-repo>
python3 -B skills/_shared/scripts/project_setup.py setup  --target <plugin-repo> [--language <tag>]
```

Behandelte Dateien: die gesyncten Dateien der konfigurierten Art, mit Hash und Ausführungsbit in der erzeugten Datei `skills/_shared/manifests/<art>.sync.json` aufgeführt (bei einem Plugin gehören der Helper `project_setup.py`, `operator_language.py` und die Flows `entry`, `language`, `skeleton`, `sync` dazu), bytegetreu aus `skills/_shared/templates/<art>/sync/` (Elternordner werden angelegt); der Helper kopiert keine Quelle, deren Bytes vom eingetragenen Hash abweichen. Dateien unter `skills/_shared/templates/<art>/seed/` legen die Generatoren nur einmal an, sie werden nie gesynct. `status` schreibt nichts. Der Skill fragt eine fehlende Sprache ab und führt dann `setup` aus; ein konkreter read-only Auftrag führt nur `status` aus.

`setup` ändert nie die Bytes einer vorhandenen Datei (außer den Verwaltungsdateien: `.gitignore` erhält die exakte Regelzeile, `.project/operator.json` speichert die Sprache, `.project/plugins/plugin-manager/skeleton.json` erhält Hashpaare). Eine von der Vorlage abweichende verwaltete Datei ist eine *Inhaltsabweichung* (unter `different` gelistet). Sie wird nur durch eine ausdrückliche `adopt`-Entscheidung der Operation `sync` ersetzt (siehe unten); Dateien werden nur nach den Entfernungsregeln unten entfernt. Ein *technischer Konflikt* (ungültiger oder nicht unterstützter Lock, beschädigte Sprachdatei, Symlink oder Traversal, Datei statt Ordner, unlesbare Datei, fehlende Vorlage, kein Ziel) stoppt vor jedem Schreibzugriff. Vor dem ersten Speichern der Sprache wird `/.project/operator.json` in `.gitignore` ergänzt (nur genau diese Zeile; andere Regeln und Negationen werden nicht ausgewertet). `.project/plugins/plugin-manager/skeleton.json` ist zur Versionierung gedacht: `{"schema_version": 2, "files": {"<Pfad>": {"source_hash": "<sha256>", "local_hash": "<sha256>"}}}`. Nur dieses Format wird unterstützt: ein älterer (v1) oder ungültiger Lock wird vor jedem Schreibzugriff abgelehnt, unverändert gelassen und nie migriert. Ein fehlender Lock ist zulässig, abweichende Dateien gelten dann aber nicht als akzeptiert. Übrige gültige Einträge bleiben.

JSON-Ergebnis: `ok`, `conflicts`, `errors`, `files` (Zustände `missing`, `identical`, `accepted`, `decision_needed`), `missing`, `identical`, `different`, `created` (einschließlich `unverified` für kopierte, aber nicht bestätigte Dateien), `language` (`needs_choice`, `saved`), `gitignore`, `lock` (`changed`, `pending`), `matches_template`. Exit-Codes: 0 Erfolg (Abweichungen oder fehlende Sprache sind keine Fehler), 1 technischer Konflikt oder Schreibfehler (Teiländerungen unter `created`), 2 ungültiger Aufruf. Kein Git, keine Installation, kein Netzwerk, kein Zielcode; der Helper und die Flows `entry`, `language`, `skeleton`, `sync` liegen byte-identisch in jedem generierten Plugin, dazu die custom Stubs (`skills/<name>/SKILL.md`, `skills/<name>/flows/configure.md`, `skills/_shared/manifests/default.json`).

Technische Fehler während des Schreibens (Symlink oder Ordner an einer bereits geprüften Datei, Lesefehler, Dateisystemfehler) erscheinen unter `conflicts`/`errors` mit Exit 1, nie als Abweichung; das Schreiben stoppt, es wird kein weiterer Locknachweis erfasst, und die tatsächlichen Teiländerungen bleiben aufgelistet. `status` weist den Verwaltungsordner `.project` unter `missing.directories` aus, solange er benötigt wird.

### Zustandsgesteuerter Einstieg

`/plugin-manager:plugin-manager` (Host-Aktivierung unter diesem Namen ungetestet) läuft als Schleife: `status` → genau den nötigen Flow ausführen → erneut `status`. `status` schreibt nichts und braucht weder `plugin.json` noch Git, Origin oder Marketplace. Felder: `state` (`plugin`, `marketplace`, `unconfigured`, `conflict`), `plugin_configured`, `next`, `language` (`operator_language`, `needs_choice`), `skeleton` (`open`, `missing_files`, `lock_pending`, `ignore_rule_pending`, `different`), `files`, `conflicts` (mit optional `code`, `entries`). `next` folgt fester Priorität: `stop` (technischer Konflikt) → `language` → `configure` (kein Konfigurationsnachweis `.project/plugins/<plugin>/config.json`) → `skeleton` → `sync` (verwaltete Datei braucht Entscheidung) → `ready`. `ready` heißt nur, dass kein automatischer Einrichtungsflow offen ist; abweichende Dateien bleiben unter `skeleton.different` sichtbar und werden weder überschrieben noch erneut geroutet.

Flows: `language --target <Ordner> --language <tag>` (erst Ignore-Regel, dann `operator_language.py`); `setup --target <Ordner>` (das Skeleton: die common-Dateien der konfigurierten Art, Elternordner, Ignore-Regel, Skeleton-Nachweis; keine erfundene `plugin.json`); danach die Konfiguration über den vorhandenen plugin-create-Generator im selben Ordner. Beide Helper-Flows antworten bei Erfolg mit `next: "status"`, bei Fehler mit `next: "stop"`. Ein Ordner ohne `plugin.json` wird akzeptiert, wenn er nur `.git/`, `.idea/` (als Ordner geprüft, nie geöffnet), eine reguläre UTF-8-`.gitignore`, gültige `.project`-Metadaten und Skeleton-Pfade enthält; anderer Inhalt (`code: not_fresh`), eine ungültige `plugin.json`, ein Marketplace oder der eingebettete Manager stoppen vor Writes. GitHub-Origin und Marketplace sind nur Voraussetzungen des Konfigurationsflows; fehlen sie, benennt der Einstieg sie und wartet, ohne das Skeleton zu entfernen. Exit-Codes wie oben.

### Sync vorhandener verwalteter Dateien

Der Lock speichert je verwalteter Datei das zuletzt akzeptierte Paar `{source_hash, local_hash}`. Regeln: lokal fehlend → kopiert, beide Hashes nach Prüfung erfasst; lokal gleich Vorlage → fehlendes oder veraltetes Paar ohne Dialog korrigiert; lokal weicht ab und das aktuelle Paar entspricht dem gespeicherten → *akzeptiert*, kein Dialog, keine Writes (und nie `matches_template`); Vorlage oder lokale Datei seit dem akzeptierten Paar geändert, oder kein Paar, bei verschiedenem Inhalt → *Entscheidung erforderlich*. `status` führt diese unter `sync.decisions` (`path`, `reason`, `source_hash`, `local_hash`, `accepted`, `source_changed`, `local_changed`, `source_file`, `local_file`) mit `next: "sync"`; es schreibt und fragt nichts. Der Skill nennt nur den Dateipfad und dass Unterschiede vorhanden sind, ohne Dateiinhalte, Textauszüge, Diff oder Inhaltszusammenfassung und fragt ausdrücklich „Lokale Datei behalten“ oder „Vorlage übernehmen“.

`sync --target <Ordner> --decision keep|adopt --path <Pfad> --source-hash <h> --local-hash <h>` wendet eine Entscheidung für genau das gezeigte Paar an: `keep` erhält die lokalen Bytes und speichert beide aktuellen Hashes; `adopt` ersetzt nur diese Datei durch die Vorlage (Modus bleibt), prüft sie und speichert `{Vorlage, Vorlage}`. Hat sich das Paar inzwischen geändert, stoppt es mit `stale_decision` ohne Schreibzugriff. Abbruch, Schweigen oder Vorauswahl ist keine Entscheidung und persistiert nichts. Exit 0 mit `ok: true` (Antwort `changed.file`, `changed.lock`, `next: "status"`) ist Erfolg; Exit 1 meldet Konflikte oder Teiländerungen. Dateien werden nur wie unter *Entfernung* beschrieben entfernt, Ordner werden nicht gehasht oder verschoben, zusätzliche lokale Dateien bleiben und `AGENTS.md` wird nicht verwaltet. Der plugin-create-Generator überschreibt eine abweichende (auch bewusst behaltene) Skeleton-Datei nie: Er stoppt offen, aufgelöst wird nur über Sync.

### Entfernung (Quelle im Parent-Template entfernt)

Die Liste verwalteter Pfade bleibt fest; ein Pfad muss darin bleiben, damit eine entfernte Quelle erkannt wird. Eine einzelne fehlende Quelle eines gelisteten Pfads bedeutet „entfernt“; eine fehlende oder ungültige Template-Basis, eine Basis ohne jede verwaltete Quelle, Symlinks, falsche Typen und Lesefehler sind technische Konflikte und nie eine Entfernung. `status` meldet `removals` getrennt: `auto` (im Besitz und unverändert: aktueller lokaler Hash gleich gespeichertem `local_hash` und `source_hash`), `decisions` (geänderte oder bewusst akzeptierte lokale Datei: wird immer gefragt), `kept` (zuvor behalten und unverändert), `unowned` (kein Locknachweis: nie angefasst) und `lock_cleanup` (Datei im Besitz bereits weg). Der Skeleton-Flow (`setup`) führt `auto` und `lock_cleanup` aus: Er löscht nur die geprüften Dateien, entfernt deren Lockeinträge und danach leere Elternordner der entfernten Dateien bottom-up mit `rmdir`; nie benötigte Skeleton-Ordner, Projektroot, `.git`, `.idea` oder `.project`, und nie fremde Dateien. Die Frage wird mit `sync --decision keep|delete --path <Pfad> --source-hash removed --local-hash <h>` beantwortet; es werden keine Dateiinhalte, Auszüge oder Diffs gezeigt. `keep` speichert `{"source_hash": null, "local_hash": "<sha256>"}` (dokumentierte Erweiterung von Lock-Schema 2, nur durch diese Entscheidung gesetzt): eine unveränderte Wiederholung fragt nicht erneut, eine spätere lokale Änderung schon, und eine zurückkehrende Quelle wird wieder normal klassifiziert. `setup` und `sync` melden `removed.files` und `removed.directories` (bei Fehlern die tatsächlichen Teiländerungen).
