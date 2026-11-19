# Usage

**Deutsch** | [English](../en/usage.md)

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.md) · [Übersicht](README.md)

## Einrichten

Zielpfade stammen aus deinem geöffneten Projekt oder einer ausdrücklichen Angabe, nie automatisch aus der Manager-Installation. Vorhandene Angaben und Git-Origin werden übernommen; nur fehlende oder widersprüchliche Angaben werden geklärt. Anzeigename und technische Kennung sind getrennte Angaben. Herausgeber, Lizenz und fachliche Skill-Inhalte werden nicht erfunden.

## Ablauf auswählen

In Claude Code: `/plugin-manager:marketplace-create`, `/plugin-manager:plugin-create` oder `/plugin-manager:configure`. In Codex/GPT die entsprechende Fähigkeit wählen oder die Aktion beschreiben. `init` wird nicht unterstützt.

Bei `plugin-create` folgen Rückfragen und Antworten der Sprache deiner aktuellen Nachricht. Bei einem reinen Slash-Befehl bleibt die bisherige Gesprächssprache erhalten; ohne Sprachkontext fragt der Agent kurz nach. Die Dokumentationssprachen werden unabhängig davon festgelegt.

Fehlende Angaben werden über den strukturierten Fragedialog des Hosts in kleinen Schritten abgefragt, sofern dieses Werkzeug verfügbar ist. Ohne Sprachkontext kommt zuerst nur die Sprachwahl; danach geht es in der gewählten Sprache weiter. Bereits bestätigte Angaben werden nicht erneut abgefragt. Ist kein Dialogwerkzeug verfügbar, erklärt der Agent das kurz und stellt jeweils eine Frage im Chat.

Vor der Erstellung klärt der Agent die Lizenzentscheidung. Eine eindeutige vorhandene Lizenz oder bereits getroffene Entscheidung wird übernommen; andernfalls fragt er nach einer Lizenz oder einer ausdrücklichen Vertagung. Ohne Antwort beginnt die Erstellung nicht. Widersprüche werden vor Änderungen geklärt und vorhandene Lizenzdateien bleiben erhalten. Eine vertagte Entscheidung erscheint im Abschlussbericht als offen. Eine gewählte Lizenz wird umgesetzt: MIT mit bestätigtem Copyright-Jahr und Rechteinhaber, andere Lizenzen anhand einer ausdrücklich bestätigten vollständigen Textdatei. Lizenzdatei, Manifest und Dokumentation werden gemeinsam erstellt und geprüft. Die Entscheidung bleibt in docs/license.md erhalten, auch bei ausdrücklicher Vertagung.

| Aktion | Eingaben | Ergebnis |
| --- | --- | --- |
| marketplace-create | Geklontes Repository, Anzeigename, Kennung, Herausgeber | Gemeinsamer Katalog, beide Host-Kataloge und eigenständige Werkzeuge |
| plugin-create | Separater Checkout/Pfad, bestehende GitHub-URL, Marketplace, Name, Kennung, Beschreibung, Herausgeber, Skill-Quelle oder Skeleton-Modus, Sprachen | Plugin-Struktur ohne eigene Kataloge, Zuordnung und Dokumentationsvorlagen |
| configure | Bestehendes Plugin und gewählter Marketplace | Katalogeintrag und lokale Zuordnung; andere Zuordnungen bleiben |

### Dokumentation aktualisieren

Nutze `update` beziehungsweise in Claude Code `/plugin-manager:update PFAD`. Die Aktion liest die aktuellen Produktquellen und die gespeicherte Sprachwahl neu, aktualisiert README und Anleitungen und prüft sie anschließend. Sie installiert nichts und veröffentlicht nichts. `update-local` ist der getrennte Befehl zum Erneuern lokaler Plugin-Snapshots.

## Ausgabe verstehen

Neue Plugins besitzen eigene Manifeste, Skills und Dokumentation, jedoch keine Marketplace-Kataloge. Der Agent vervollständigt erzeugte Dokumentationsvorlagen aus den Quellen. `valid` und `structure_valid` bewerten die veröffentlichbare Struktur. `local_development.complete` bewertet getrennt die lokale Entwicklungskonfiguration. Fehlende Checkouts oder `.local`-Dateien sind bei frischen Clones erwartbar und machen den veröffentlichten Katalog nicht ungültig. Die Prüfung führt keinen Zielcode aus.

## Sitzung steuern

Vorhandene Dateien werden zuerst geprüft. Abweichende Werkzeugdateien und widersprüchliche Zuordnungen stoppen den Ablauf zur gezielten Klärung; persönliche Daten und Installationen bleiben erhalten. Fehlende Checkouts werden nur bei plugin-create aus der angegebenen bestehenden GitHub-Quelle geklont. Configure migriert keine alten Plugin-Kataloge automatisch.

## Später fortsetzen

Update liest aktuelle Quellen erneut. Publish kann mit einem privaten Journal fortgesetzt werden, nachdem tatsächlicher GitHub-Stand und ursprüngliche Freigabe überprüft wurden. Alte Release-Journals benötigen einen neuen Plan.

## Spezialisierte Abläufe

`make install-local TARGET=claude|codex` und `make update-local` verwenden alle zugeordneten Plugins in einem gemeinsamen `<marketplace-id>-dev`. Im Plugin überschreibt `MARKETPLACE=/pfad/zum/katalog` den lokalen Standard nur für den Aufruf. Fehlende benötigte Checkouts stoppen vor Host-Änderungen. `DRY_RUN=1` erzeugt nur Snapshots.

[Publish](publish.md) behandelt Plugin und Marketplace getrennt: bei neuen Einträgen zuerst Plugin, danach Marketplace. Branch → Commit → Push → PR → Prüfungen → Merge erfordern eine konkrete Freigabe. Keine Tags, Releases oder Plugin-ZIPs.

[Technische Aufrufe und Eingaben](../../skills/_shared/references/workflows.md)

Lokale Zuordnungen werden erst geschrieben, nachdem Git die vorgeschlagenen Ignore-Regeln als wirksam bestätigt hat. Negationen, die `.local/marketplace.json` sichtbar machen, stoppen vor Änderungen; bestehende Inhalte und Zuordnungen bleiben erhalten. [Erstveröffentlichung ohne HEAD](publish.md#erstveröffentlichung-ohne-head) erfordert eine eigene ausdrückliche Freigabe.

Lokale Snapshots lesen den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `update-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR ist für lokale Tests erforderlich. Es bleibt bei einem gemeinsamen `<marketplace-id>-dev`, ohne zusätzliche Marketplaces pro Branch.

`configure` ist der reguläre Einrichtungsweg. `local-marketplace.example.json` ist eine optionale manuelle Kopiervorlage. Nur `.local/marketplace.json` wird zur Laufzeit für lokale Zuordnungen gelesen; diese Zuordnungen werden nicht committed.

### Skeleton vor der fachlichen Implementierung

Neue Skeleton-Seiten werden in den gewählten Sprachen mit dem tatsächlichen Gerüststatus ausgefüllt und vor dem Schreiben validiert. Vorhandene Texte bleiben erhalten. Die Abschlussprüfung bewertet anschließend die tatsächliche Plugin-Struktur, den Marketplace und die Dokumentation getrennt. Fehler in erhaltenen Seiten bleiben sichtbar; `checks.status=needs_attention` bedeutet, dass die Erstellung noch offene Prüfbefunde hat. `passed` prüft auch die technische Konsistenz von Lizenzdateien und Dokumentation; das ist keine rechtliche Bewertung oder fachliche Abnahme. Der Abschlussbericht nennt außerdem die Lizenzentscheidung, tatsächliche Lizenzdateien und noch ausstehende Tests beziehungsweise Host-Prüfungen.

`plugin-create --skeleton` erstellt ein ausdrücklich unfertiges Plugin, auch wenn es noch keine fachliche Skill-Quelle gibt. Marketplace, technische Kennung, Anzeigename, vorhandenes GitHub-Repository, Herausgeber und Dokumentationssprachen werden aus bekannten Angaben übernommen oder gezielt geklärt. Die Beschreibung ist optional; ohne bestätigte Beschreibung steht ausdrücklich „unimplemented“ im Manifest. Keine fachlichen Funktionen oder Lizenz werden erfunden.

```sh
# Im ai.plugins-Checkout; Zielrepository existiert bereits lokal mit Git-Origin:
make plugin-create ARGS='--root /pfad/zum/plugin --marketplace /pfad/zum/katalog --skeleton --name beispiel-plugin --display-name "Beispiel Plugin" --author "Bestätigter Herausgeber" --languages de en --default-language de --license deferred'
```

Der Modus `--source /pfad/zum/skill` importiert ausdrücklich gewählte Skill-Quellen; beide Modi schließen sich aus. Das Skeleton besitzt einen nicht funktionalen Skill mit sichtbarer Markierung, Manifeste, Zuordnung, Dokumentationsgerüst, Testwerkzeuge, `SCOPE.md`, `AGENTS.md`, `CLAUDE.md` und `docs/architecture.md`. Abweichende vorhandene Anweisungen oder SCOPE-Dateien werden nicht überschrieben. Eine gültige Struktur ist keine fachliche Abnahme.

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
