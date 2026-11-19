# Prüfstand

## Aktuelle Formatgrenze (19.11.2026)

Es gilt ausschließlich das aktuelle Regelwerk: keine Altformat-Unterstützung, Ersatzpfade oder automatische Migration. Frühere Prüfstände unten sind historische Nachweise und keine Zusage heutiger Kompatibilität. Benutzerdaten bleiben bei Ablehnung unverändert.

## Modelltests des Zielbild-/Source-Reviews (19.11.2026)

Sechs fiktive Fälle wurden jeweils mit Claude Code 2.1.319 (laut Nutzungsmetadaten claude-sonnet-5-5) und Codex CLI 0.165.0 (CLI-Standardmodell, genaue Modellkennung nicht in den erfassten Ereignissen ausgewiesen) ausgeführt. Beide erhielten dieselben Review-Regeln, vollständige fiktive Dateien und beobachtete statische Berichte; die erwarteten Ergebnisse wurden nicht übermittelt. Tools waren deaktiviert/eingeschränkt, die Source wurde nicht ausgeführt.

Der erste automatische Lauf ergab Claude 4/6 und Codex 6/6. Die manuelle Sichtung zeigte bei Claude eine Vermischung von Source-Bewertung und Testabdeckung sowie einen nicht geforderten Test-Randfall. Daraufhin wurde der gemeinsame Review-Vertrag präzisiert. Zwei Auswerter-Fehlalarme (weggelassene Einrückung im Zitat und die ausdrücklich zurückgewiesene, nur beschriebene Erfolgsanweisung) wurden mit Regressionstests korrigiert. Erstläufe und ursprüngliche Auswertungen bleiben unverändert erhalten.

Im vollständigen Wiederholungslauf wurden alle Antworten manuell gesichtet und mit dem korrigierten Auswerter erneut bewertet: **Claude 6/6, Codex 6/6**. Beide korrekten Plugins blieben ohne Defekt-/Testlücken-Fehlalarm; echter Schreibfehler, inhaltsleerer Test und fehlende Source wurden passend eingeordnet. Kein Bericht behauptete ausgeführte Tests, Runtime-Abnahme oder Veröffentlichungsreife. Die eingeschleuste Erfolgsanweisung wurde ignoriert. Alle fiktiven Zielverzeichnisse blieben bytegleich.

[Versionierter Ergebnisnachweis](../../tests/behavior/evidence/review-models-2026-11-19.json). Rohantworten, Prompts und Diagnosen bleiben getrennt im ignorierten .tmp-Verzeichnis. Diese 24 Modellaufrufe (Erst- und Wiederholungsläufe) sind ein begrenzter Prompt-Test, keine statistische Zuverlässigkeitsgarantie oder freie Host-/Tool-Abnahme. Textheuristiken benötigen weiterhin manuelle Sichtung. Keine persönlichen Plugin-Installationen verändert, keine Commits oder Pushes.

## Skeleton und Zielbild-/Source-Review (19.11.2026)

plugin-create unterstützt ausdrücklich --skeleton ohne fachliche Quelle sowie weiterhin --source. Neue Gerüste enthalten draft-SCOPE.md, AGENTS.md, CLAUDE.md und Architekturregeln. Verify kennzeichnet Skeletons getrennt von struktureller Gültigkeit und bietet --review für statische, lesende Belegprüfung. Der anschließende fachliche Agent-Vergleich hat einen eigenen Berichtvertrag; verfügbare Dateiverweise sind keine fachliche oder Test-Abnahme.

Der vollständige deterministische Lauf bestand 146 Tests (25 Marketplace-, 121 Manager-Tests), native Abnahme separat vier Tests ohne Überspringen in isolierten Claude-/Codex-Profilen. Gezielte Create- und Review-Tests bestanden auch nach den abschließenden Anpassungen. Befunde prüfen fehlendes Zielbild, draft-Anforderungen, sichere Dateigrenzen, Skeletons, Runtime-Abhängigkeiten auf Entwicklungswerkzeuge und unveränderte Quelldateien. Ein absichtlich widersprüchlicher Source wird von der Belegprüfung niemals als fachlich erfüllt behauptet. Modellbasierte Review-Evaluationen wurden nicht ausgeführt; Rückfragedialoge und fachliche LLM-Zuverlässigkeit bleiben separat zu prüfen. Keine persönlichen Installationen verändert; nichts committed oder gepusht.

## Einheitliche Teststruktur (19.11.2026)

Alle bisherigen 212 Testmethoden aus Marketplace, Manager und Coach sind erhalten. Tests sind zuerst nach Typ, danach bei Bedarf nach Skill/Komponente geordnet. Vier zusätzliche Tests sichern die Teststeuerung ab; ein weiterer prüft die Make-Testbefehle frisch erzeugter Repositories. `make test` bestand 134 deterministische Tests in ai.plugins einschließlich Manager und 79 im Coach. `make test-native` bestand separat vier Tests in isolierten Claude-/Codex-Profilen, keiner übersprungen. Modelltests wurden nicht ausgeführt; der Coach besitzt derzeit keine eigene native Suite. Frühere Native-Flags bei make test sind historische Aufrufe; aktuell ist test-native der ausdrückliche Einstieg. Keine persönlichen Installationen verändert, keine Commits oder Pushes.

## Sieben Skills (19.11.2026)

Die sechs öffentlichen Skills heißen marketplace-create, plugin-create, configure, verify, update und publish. Gemeinsame Regeln, Helfer und Vorlagen liegen unverändert inhaltlich gebündelt unter skills/_shared; es gibt dort keine SKILL.md. Onboarding verweist auf den lesenden verify-Skill. Explizite Prüfvarianten und der init-Hinweis bleiben Befehle.

Der vollständige native Testlauf bestand 133 Tests (23 Marketplace-, 110 Manager-Tests), ohne übersprungene Tests. Neue Regressionen prüfen die genaue Skill-Menge, Frontmatter, gemeinsame Ressourcen in beiden Host-Paketen sowie die Befehlszuordnung. Die bisherigen Publish-, Ignore- und Codex-Manifest-Regressionen bestanden weiterhin. Native Tests verwendeten ausschließlich temporäre Repositories und isolierte Host-Profile. Keine persönlichen Installationen verändert; nichts committed, gepusht oder veröffentlicht. GitHub-/GUI-Abnahme bleibt separat.

## Dokumentationsabgleich am 19.11.2026

`update` hat die aktuellen Quellen beider Repositories erneut abgeglichen. Deutsch/Englisch, Skill-Pfade, Einrichtung über configure, lokale Snapshots, Veröffentlichungsfreigaben und historische Nachweise sind abgestimmt. Dokumentationsvalidierung, Manifest-/Katalogprüfung, Verify und lokale Marketplace-README-Links bestanden. Coach: 79 Tests bestanden. ai.plugins einschließlich Manager: 130 Tests erfasst, 126 bestanden und vier optionale native Tests bewusst übersprungen. Kein neuer Host-/GUI-Test und keine Modellaufrufe. Keine persönlichen Installationen verändert, keine Commits, Pushes oder Veröffentlichungen.

## Bestätigte Beobachtungen

Am 18.11.2026 bestätigte der Nutzer: „Import hat bei Claude + GPT geklappt.“ Zuvor wurden lokale CLI-Importe in isolierten Claude- und Codex-Profilen geprüft. Das Repository war als `draftm0de/zyris.skill.manager` nach Commit `58edc2b` verfügbar.

## Grenzen

Die Bestätigung betrifft den Erstimport. Sie ist kein vollständiger Funktions-, Update-, Deinstallations- oder Publish-Test. Aktuelle lokale Prüfergebnisse sind im jeweiligen Arbeitsbericht festzuhalten; alte Testzahlen werden nicht als Beleg neuer Änderungen übernommen. Für neu erzeugte Plugins ist eine eigene Host-Abnahme erforderlich.

## Nächster Host-Test

Nach einem später freigegebenen Push den Marketplace aktualisieren, einen neuen Chat öffnen und die geänderten Create-/Configure-/Verify-/Publish-Regeln prüfen. Keine produktive Veröffentlichung zum Testen auslösen. Die hier überarbeiteten Regeln sind bis zu diesem Push nur lokal vorhanden.

[Installation](installation.md) · [Publish](publish.md)

## Lokale Abnahme am 19.11.2026

Für den uncommitteten Arbeitsstand auf Basis von ai.plugins `65c1ecb` bestanden 112 Tests (21 Marketplace-Tests und 91 Manager-Tests), ohne übersprungene Tests, mit:

```sh
PLUGIN_MANAGER_NATIVE=1 ZYRIS_TEST_SHARED_LOCAL=1 ZYRIS_TEST_LOCAL_NATIVE=1 make test
```

Geprüft wurden Erstellung eines neuen Marketplaces ohne eingebetteten Manager, separates Plugin, Anbindung eines bestehenden Plugins, Erhalt anderer Zuordnungen und expliziter lokaler Override, Konflikte und Symlinks, unveränderte fremde Inhalte sowie fehlende lokale Konfiguration bei gültiger veröffentlichbarer Struktur. Ein echter Git-Clone gegen ein temporäres lokales Fixture prüfte den fehlenden Checkout; GitHub-Zugangsdaten und Netzwerkzugriff waren dabei nicht beteiligt.

Native Claude-/Codex-Tests verwendeten ausschließlich temporäre Profile. Beide Plugins wurden installiert, ohne Commit geändert und aktualisiert; die tatsächlich geladenen Skill-Dateien wurden mit den Arbeitsständen verglichen. Zusätzlich lief der Create-Ablauf aus einer isolierten Manager-Kopie außerhalb des Entwickler-Checkouts. Publish-Tests prüften getrennte Marketplace-Pläne, erforderliche Plugin-Nachweise und ungültig gewordene Freigaben ohne Veröffentlichung.

`make check-plugin`, `make verify`, `make plugin-verify SOURCE=../ai.plugin.interview-coach`, `make validate-docs` und `git diff --check` waren erfolgreich. Die beiden realen Repository-Strukturen und ihre vorhandene lokale Zuordnung sind gültig; der Coach-Checkout blieb unverändert auf `edaf2d9`.

Diese Beobachtungen sind lokale Werkzeug-/CLI-Abnahme. Nicht geprüft sind die Veröffentlichung dieser Änderungen, GitHub-Clone mit echten Zugangsdaten, die spätere GUI-Installation/-Aktualisierung und ein vollständiger Live-Publish. Erzeugte Dokumentationsvorlagen müssen weiterhin anhand bestätigter Produktquellen vervollständigt werden; Lizenz und fachlicher Skill-Inhalt werden nicht erfunden. Persönliche Host-Installationen wurden nicht als Testziele verwendet.

## Cross-Review: gezielte Regressionen

Nach den drei Korrekturen bestanden 119 Tests (21 Marketplace-, 98 Manager-Tests), ohne übersprungene Tests, mit demselben vollständigen nativen Testaufruf. Die Erstveröffentlichung für Plugin und Marketplace wurde mit tatsächlichen ersten Commits und Pushes ausschließlich in temporäre lokale Bare-Repositories geprüft. Vorbereitung und Freigabe allein ließen HEAD und Arbeitsdateien unverändert; fehlende Initial-Freigabe und fehlende PR-Basis wurden abgewiesen.

Root- und verschachtelte Ignore-Negationen wurden reproduziert: configure/plugin-create brachen vor Änderungen ab, bestehende Zuordnungen blieben bytegleich. Die normale erzeugte lokale Konfiguration war für Git tatsächlich ignoriert. Änderung, Hinzufügen und Entfernen des nicht ausgewählten Codex-Manifests machten Freigaben ungültig. Schema-1/2-Journale benötigen einen neuen Plan. Metadaten-, Struktur-, Dokumentationsprüfung und diff --check waren erfolgreich. Keine Veröffentlichung auf GitHub und keine Änderungen an persönlichen Host-Installationen; GitHub-/GUI-Abnahme bleibt ausstehend.

## Feature-Branch, Voraussetzungen und lokale Entwicklung

Nach der gezielten Nachschärfung bestanden 130 Tests (23 Marketplace-, 107 Manager-Tests), keiner übersprungen, mit dem vollständigen nativen Testaufruf oben. Zusätzliche Regressionen prüfen Branch-Anlage erst nach Freigabe, neutrale Namen, Sperre des Default-/Basisbranches, Namenskollisionen, Wiederaufnahme einschließlich unterbrochener Branch-Anlage sowie fehlende/geänderte Branches. Commit-Belege auf dem Default-Branch werden abgewiesen. Fehlende GitHub-Fähigkeiten werden konkret gemeldet; der Bootstrap, wirksame Ignore-Prüfungen und die Codex-Manifest-Bindung bleiben abgedeckt.

Lokale Snapshots wurden nach Branchwechsel und uncommitteten Änderungen im selben Entwicklungskatalog geprüft. Direkte Python-Aufrufe für Snapshots und Verify liefen mit leerem PATH ohne Make oder Host-CLI. Eine fehlerhafte optionale Beispiel-JSON beeinflusste die Laufzeit nicht; bei fehlender .local-Konfiguration wurde nicht darauf zurückgegriffen. Die Vorlagenkopien der zentralen Voraussetzungen sind bytegleich geprüft.

Metadaten-, Struktur-, Dokumentationsprüfung und diff --check bestanden. Das Arbeitsrepository blieb auf main bei 65c1ecb, der Coach unverändert. Branch-/Commit-/Push-Aktionen fanden ausschließlich in temporären Test-Repositories statt; persönliche Host-Installationen blieben unverändert. Schema-4-Pläne benötigen neue Freigaben; tatsächliche GitHub-Connector-/gh-Rechte und GitHub-/GUI-Veröffentlichung werden erst bei einem ausdrücklich beauftragten Publish-Lauf geprüft.
