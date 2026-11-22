# Draftmode AI Plugins

**Deutsch** | [English](README.en.md)

Marketplace für Claude und Codex. Repository: https://github.com/draftm0de/ai.plugins

| Plugin | Technischer Name | Quelle |
| --- | --- | --- |
| [Plugin Manager](plugins/plugin-manager/README.md) | `plugin-manager` | Lokal: `./plugins/plugin-manager` |
| [Interview Coach](https://github.com/draftm0de/ai.plugin.interview-coach) | `interview-coach` | Externes GitHub-Repository |

## Skills und ihre Aufgaben

`plugin-manager` ist das Plugin und bündelt sechs Skills. Wähle den passenden Skill für dein Zielrepository. Gemeinsame Regeln, Werkzeuge und Vorlagen liegen unter [`skills/_shared/`](plugins/plugin-manager/skills/_shared/WORKFLOWS.md); dafür gibt es keinen eigenen Manager-Skill.

| Skill | Aufgabe |
| --- | --- |
| [marketplace-create](plugins/plugin-manager/skills/marketplace-create/SKILL.md) | Marketplace in einem bestehenden lokalen GitHub-Checkout einrichten: Manifest, Host-Kataloge, Werkzeuge und Dokumentationsgerüst. |
| [plugin-manager](plugins/plugin-manager/skills/plugin-manager/SKILL.md) | Sprache einrichten, Skeleton synchronisieren und ein neues Plugin über den zentralen Einstieg konfigurieren. |
| [verify](plugins/plugin-manager/skills/verify/SKILL.md) | Repository-Typ erkennen und nur lesend prüfen. Veröffentlichbare Struktur und verfügbare lokale Entwicklungskonfiguration getrennt bewerten. |
| [update](plugins/plugin-manager/skills/update/SKILL.md) | README und Dokumentation anhand aktueller Quellen und gespeicherter Sprachwahl pflegen. Keine Installation oder Veröffentlichung. |
| [publish](plugins/plugin-manager/skills/publish/SKILL.md) | Veröffentlichung für Plugin oder Marketplace planen. Erst nach konkreter Freigabe über Feature-Branch, Commit, Push, PR, Checks und Merge ausführen. |

`plugin-verify` und `marketplace-verify` bleiben explizite Prüfvarianten als Befehle, keine eigenen Skills. `init` wird nicht unterstützt; verwende ausdrücklich marketplace-create oder plugin-manager.

### Verwendung und Abgrenzung

In Claude Code beispielsweise `/plugin-manager:marketplace-create`, `/plugin-manager:plugin-manager`, `/plugin-manager:verify`, `/plugin-manager:update`, `/plugin-manager:publish` verwenden. In Codex den aktuell benannten Skill wählen oder die Aufgabe mit dem Zielrepository beschreiben. [Eingaben und Beispiele](plugins/plugin-manager/docs/de/usage.md).

`update` pflegt Dokumentation. `install-local` erstellt lokale Plugin-Snapshots einschließlich uncommitteter Änderungen. `install-local`, Metadaten-Synchronisierung und Dokumentationsvalidierung sind Werkzeugfunktionen, keine zusätzlichen Skills. Create legt kein GitHub-Repository an und erfindet keine fachlichen Skill-Inhalte. Publish behandelt Plugin und Marketplace getrennt; der ausdrücklich freizugebende Bootstrap vollständig leerer Repositories bleibt die dokumentierte Ausnahme vom PR-Ablauf.

**Interview Coach** bündelt den Skill `interview-coach` für Interviewtraining, gezielte Vorbereitung, Feedback und optionalen privaten Lernstand. Er gehört zum separaten Plugin-Repository; [Aufgaben und Modi](https://github.com/draftm0de/ai.plugin.interview-coach#funktionen-und-modi).

## Installation

Füge `https://github.com/draftm0de/ai.plugins` in der Plugin-Verwaltung als Marketplace hinzu und wähle **Plugin Manager** oder **Interview Coach**. Die Marketplace-Kennung ist `draftmode-ai-plugins`.

Claude Desktop: Einstellungen → Anpassungen → Plugins → + Hinzufügen → Marketplace hinzufügen → Aus einem Repository hinzufügen.

Codex: User Icon → Settings → Integration → Plugins → + Add → A Marketplace.

## Entwicklung

Dieses Handbuch beschreibt den Weg vom lokalen Checkout bis zur Veröffentlichung. `ai.plugins` verwaltet den Marketplace; jedes neue Plugin erhält ein separates Repository. Der bestehende `plugin-manager` unter `plugins/plugin-manager/` bleibt die einzige eingebettete Ausnahme.

- [Marketplace](#marketplace): [Erstellen/Einrichten](#marketplace-erstellen) · [Katalog pflegen und prüfen](#marketplace-pruefen) · [Veröffentlichen](#marketplace-veroeffentlichen) · [Dokumentation](#marketplace-dokumentation)
- [Plugin](#plugin): [Erstellen/Einrichten](#plugin-erstellen) · [Lokal bereitstellen](#plugin-lokal) · [Testen](#plugin-testen) · [Dokumentation](#plugin-dokumentation) · [Veröffentlichen](#plugin-veroeffentlichen)

**Voraussetzungen:** Git und Python 3.10+; Make dient als Komfortzugang. Für automatische lokale Installation und Aktualisierung wird die jeweilige Claude-/Codex-CLI benötigt, für Modelltests zusätzlich deren Authentifizierung. Die Verwaltungswerkzeuge benötigen keine zusätzlichen Python-Pakete. [Alle Voraussetzungen](plugins/plugin-manager/skills/_shared/references/prerequisites.md).

**Im Chat arbeiten:** Voraussetzung ist, dass der Marketplace hinzugefügt und **Plugin Manager** installiert und in der Sitzung verfügbar ist. Verwende eine lokale Claude-/Codex-Umgebung mit Zugriff auf deine Projektdateien und Entwicklungswerkzeuge. Lege ein Projekt an oder öffne ein bestehendes, wähle den jeweiligen Repository-Ordner als Arbeitsordner und starte darin einen Chat. Die genaue Projektauswahl hängt vom Host ab; entscheidend ist der lokale Zielordner. Die Installation des Plugins allein gibt einem reinen Web-Chat keinen Zugriff auf deinen Checkout.

In Claude Code startest du den passenden Befehl, etwa `/plugin-manager:marketplace-create`; in Codex wählst du den Skill oder nennst ihn ausdrücklich im Auftrag. Gib zusätzliche Repository-Pfade im Chat an. Ziel ist immer dein ausgewähltes Projekt oder der ausdrücklich genannte Ordner, niemals automatisch das Installationsverzeichnis des Managers.

**Im Terminal arbeiten:** Die Make-Beispiele für Create und Configure setzen einen lokalen Checkout von `ai.plugins` voraus und laufen in dessen Stamm. Die Installation des Managers allein stellt dort kein Makefile bereit. Andere Befehle laufen im jeweils angegebenen Repository. Platzhalter wie `../mein-plugin` und Herausgeberangaben durch die eigenen Werte ersetzen. Die Chat-Abläufe nutzen dieselben Werkzeuge; deren technische Voraussetzungen gelten ebenfalls.

### Marketplace

<a id="marketplace-erstellen"></a>

#### Erstellen/Einrichten

**Im Chat**

1. Ein GitHub-Repository anlegen und lokal klonen.
2. In Claude/Codex ein Projekt für diesen Checkout anlegen oder öffnen und dessen Ordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `marketplace-create` wählen oder in Claude Code `/plugin-manager:marketplace-create` aufrufen.
5. Den Auftrag mit technischer Kennung, Anzeigename und Herausgeber formulieren. Bereits bekannte Angaben und Git-Origin werden übernommen; fehlende oder widersprüchliche Angaben werden geklärt.

> Führe marketplace-create im ausgewählten Projektordner aus. Die Kennung ist mein-katalog, der Anzeigename „Mein Katalog“ und der Herausgeber „Bestätigter Herausgeber“. Richte den Marketplace ein und prüfe anschließend die Struktur.

**Im Terminal** – aus dem `ai.plugins`-Checkout:

```sh
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py marketplace-create --root ../mein-marketplace --name mein-katalog --display-name "Mein Katalog" --owner "Bestätigter Herausgeber"
```

Das erzeugt `marketplace.json`, die Host-Kataloge für Claude und Codex, eigenständige Werkzeuge, Makefile und ein Dokumentationsgerüst. Neue Marketplaces benötigen keinen eingebetteten Manager. Vorhandene Inhalte werden zuerst geprüft; abweichende Dateien werden nicht still überschrieben.

Für die Arbeit an **diesem** Marketplace ist kein erneuter Create-Aufruf nötig. Bestehende Plugin-Checkouts über `plugin-manager` (associate) zuordnen; neue Plugins über `plugin-manager` hinzufügen, wie im [Plugin-Abschnitt](#plugin-erstellen) beschrieben.

<a id="marketplace-pruefen"></a>

#### Katalog pflegen und prüfen

`marketplace.json` ist die kanonische Katalogkonfiguration. Nach Änderungen die Host-Kataloge erzeugen und prüfen.

**Im Chat:** Das Marketplace-Projekt öffnen und die Schritte ausdrücklich beauftragen:

> Synchronisiere die Host-Kataloge dieses Marketplaces, prüfe sie mit verify und führe anschließend die regulären Tests aus. Berichte Strukturprüfung und Testergebnisse getrennt.

`verify` allein startet keine Tests und synchronisiert keine Dateien.

**Im Terminal** – im jeweiligen Marketplace-Stamm:

```sh
make sync-marketplace
make check-marketplace
make verify
make test
```

In `ai.plugins` berücksichtigen `make sync-plugin` und `make check-plugin` zusätzlich die Metadaten des eingebetteten Managers. `make test` führt hier sowohl die Marketplace- als auch die Manager-Tests aus.

Lokale Checkout-Pfade stehen in der Git-ignorierten `.local/marketplace.json` unter `sources`. Die Zuordnung eines Plugins richtet `plugin-manager` (associate) ein und ändert sie; ein Plugin speichert den Pfad seines einen Marketplace in der von Git ignorierten `.project/plugins/plugin-manager/local.json`. Optional kann `local-marketplace.example.json` als manuelle Kopiervorlage dienen; relative Pfade beziehen sich auf die Marketplace-Wurzel.

Die Prüfung trennt `structure_valid` von `local_development.complete`: Ein frischer Clone kann ohne lokale Zuordnungen strukturell gültig sein. Für die lokale Installation müssen dagegen alle benötigten Plugin-Checkouts verfügbar sein. [Lokale Bereitstellung](#plugin-lokal) · [Testübersicht](tests/README.md).

<a id="marketplace-veroeffentlichen"></a>

#### Veröffentlichen

**Im Chat**

1. Das Marketplace-Projekt öffnen.
2. Den Marketplace-Ordner als Arbeitsordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `publish` wählen oder in Claude Code `/plugin-manager:publish` aufrufen.

Auftrag: „Führe publish für diesen Marketplace aus und bereite den Veröffentlichungsplan zur Freigabe vor.“ Der Ablauf besteht aus Vorbereitung, konkreter Freigabe einschließlich Feature-Branchnamen, Branch, Commit, Push, PR, Checks und Merge. Publish benötigt einen ausreichend leistungsfähigen GitHub-Connector oder authentifiziertes `gh` mit den erforderlichen Rechten.

Neue oder geänderte Plugin-Quellen zuerst in ihrem eigenen Repository veröffentlichen und prüfen, danach den zugehörigen Marketplace-Eintrag veröffentlichen. Plugin und Marketplace erhalten getrennte Veröffentlichungspläne. Der ausdrücklich freigegebene Bootstrap eines vollständig leeren Repositorys ist die dokumentierte Ausnahme vom PR-Ablauf.

Nach Veröffentlichung den Marketplace in Claude beziehungsweise Codex synchronisieren und die angebotenen Plugins prüfen. Für diesen Katalog müssen **Plugin Manager** und **Interview Coach** sichtbar und installierbar sein. Der Coach wird über den Default-Branch seines Repositorys ohne Tag- oder Versionsbindung referenziert; beide Repositories müssen zugänglich sein. Lokale CLI-Tests ersetzen diese GitHub-/GUI-Abnahme nicht.

Es werden keine Release-Actions, Tags oder Plugin-ZIPs benötigt. [Freigabe und Wiederaufnahme](plugins/plugin-manager/docs/de/publish.md).

<a id="marketplace-dokumentation"></a>

#### Dokumentation

Die Marketplace-READMEs beschreiben Katalog, Installation und Entwicklungsabläufe.

**Im Chat**

1. Das Marketplace-Projekt öffnen.
2. Den Marketplace-Ordner als Arbeitsordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `update` wählen oder in Claude Code `/plugin-manager:update` aufrufen.

Auftrag: „Führe update für ai.plugins aus und prüfe anschließend beide READMEs auf Inhalt und lokale Links.“ Quellen werden dabei neu gelesen und die vorhandenen Sprachfassungen gepflegt.

```sh
# Im Stamm von ai.plugins:
make validate-docs
```

Dieser Aufruf validiert die Dokumentation des eingebetteten Managers. Die Marketplace-READMEs zusätzlich inhaltlich und auf lokale Links prüfen. Ausführliche Manager-Anleitungen liegen unter [`plugins/plugin-manager/docs/`](plugins/plugin-manager/docs/de/README.md).

### Plugin

<a id="plugin-erstellen"></a>

#### Erstellen/Einrichten

Ein neues Plugin gehört in ein separates GitHub-Repository mit eigenen Manifesten, Skills und Dokumentation. Es enthält keinen eigenen Marketplace-Katalog. Das GitHub-Repository muss bereits existieren; ein fehlender lokaler Checkout kann über `--repository` geklont werden.

**Im Chat**

1. Ein separates GitHub-Repository für das Plugin anlegen. Für die direkte Projektauswahl lokal klonen und den Checkout als neues Projekt in Claude/Codex öffnen.
2. Den Plugin-Ordner als Arbeitsordner auswählen. Den lokalen Marketplace-Pfad bereithalten; der installierte Katalog ersetzt keinen Marketplace-Checkout.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `plugin-manager` wählen oder in Claude Code `/plugin-manager:plugin-manager` starten. Die Erstellung legt ausschließlich ein Skeleton an.
5. Namen, Herausgeber, Marketplace und Dokumentationssprachen nennen, soweit sie noch nicht aus dem Projekt bekannt sind.

> Führe plugin-manager für dieses Projekt als Skeleton aus. Verwende den Marketplace unter ../mein-marketplace, die Kennung mein-plugin, den Anzeigenamen „Mein Plugin“ und den Herausgeber „Bestätigter Herausgeber“. Dokumentiere auf Deutsch und Englisch mit Deutsch als Standard. Kläre anschließend mit mir das Zielbild in SCOPE.md.

Den ausdrücklich ausgewählten Plugin-Checkout vor dem zentralen Aufruf als Projekt öffnen.

**Im Terminal** – ein neues Plugin als Skeleton erstellen:

| Ausgangslage | Option | Ergebnis |
| --- | --- | --- |
| Die fachliche Umsetzung beginnt erst | `--skeleton` | Ein noch nicht funktionsfähiges Gerüst mit zu bestätigender `SCOPE.md` entsteht. |

Beispiel für ein Skeleton in einem bereits geklonten Repository:

```sh
# Im Stamm von ai.plugins:
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py plugin-create --root ../mein-plugin --marketplace . --skeleton --name mein-plugin --display-name "Mein Plugin" --author "Bestätigter Herausgeber" --languages de en --default-language de --license deferred
```

`--license deferred` setzt eine ausdrücklich vertagte Lizenzentscheidung voraus. Für MIT stattdessen `--license MIT --copyright-year "BESTÄTIGTES_JAHR" --copyright-holder "BESTÄTIGTER_RECHTEINHABER"` verwenden; andere Lizenzen benötigen `--license KENNUNG --license-file /pfad/zum/bestätigten-lizenztext`.

Ein Skill-Import ist nicht unterstützt. `python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py plugin-create --help` zeigt alle Optionen.

`plugin-create` erzeugt Entwicklungswerkzeuge und Dokumentationsvorlagen, trägt das Plugin im Marketplace ein und richtet lokale Zuordnungen ein. Beim Skeleton anschließend das Zielbild in `SCOPE.md` bestätigen, die Skills implementieren und passende Tests ergänzen. Strukturprüfung allein bestätigt noch kein fertiges Produkt.

Ein Plugin gehört zu genau einem Marketplace. Um seine Zuordnung neu einzurichten (frischer Clone, verschobener Checkout) oder es in einen anderen Marketplace zu verschieben, dient der Flow `associate` von `plugin-manager`.

**Im Chat**

1. Das Plugin-Projekt öffnen.
2. Den Plugin-Ordner als Arbeitsordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. In Claude Code `/plugin-manager:plugin-manager` aufrufen und um die Änderung der Marketplace-Zuordnung bitten.

Den Auftrag beispielsweise so formulieren:

> Ändere die Marketplace-Zuordnung dieses Plugins auf den Marketplace unter ../mein-marketplace.

Alternativ im Terminal aus dem `ai.plugins`-Checkout:

```sh
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py associate --root ../mein-plugin --marketplace .
```

Die Identität `marketplace {name, repository}` des Plugins steht in seiner committeten `.project/plugins/plugin-manager/config.json`, der Pfad des Checkouts in der von Git ignorierten `.project/plugins/plugin-manager/local.json`; der Marketplace hält die Checkouts seiner Plugins unter `sources` in seiner `.local/marketplace.json`. Ein Wechsel verschiebt den Katalogeintrag in einer Transaktion; lokale Pfade werden nicht committet. [Create-/Associate-Anleitung](plugins/plugin-manager/docs/de/usage.md) · [Technische Optionen](plugins/plugin-manager/skills/_shared/references/workflows.md).

<a id="plugin-lokal"></a>

#### Lokal bereitstellen

**Im Chat:** Das Plugin- oder Marketplace-Projekt öffnen und den gewünschten Host nennen:

> Stelle die zugeordneten Plugins aus den lokalen Checkouts mit install-local für Codex bereit.

Nach Änderungen oder einem Branchwechsel:

> Aktualisiere die lokalen Plugin-Snapshots mit install-local für Codex, einschließlich meiner uncommitteten Änderungen.

Für Claude entsprechend „für Claude“ angeben. `install-local` ist eine Werkzeugaktion, kein eigener Skill und kein Slash-Befehl. Der Agent führt die Repository-Werkzeuge aus; die jeweilige Host-CLI muss verfügbar sein.

**Im Terminal** – nach der Zuordnung im Marketplace- oder eingerichteten Plugin-Repository:

```sh
make install-local TARGET=claude
# Alternativ für Codex:
make install-local TARGET=codex
```

Die Installation erstellt gefilterte Snapshots unter `dist/local-development/` und stellt **alle zugeordneten Plugins** im gemeinsamen `<marketplace-id>-dev` bereit. Für diesen Marketplace heißt er `draftmode-ai-plugins-dev`. Alle benötigten Checkouts müssen vor dem Host-Aufruf verfügbar sein.

Nach Änderungen oder einem Branchwechsel die Snapshots erneuern:

```sh
make install-local TARGET=claude
# Alternativ für Codex:
make install-local TARGET=codex
```

Anschließend eine neue Host-Sitzung öffnen und die gewünschte Entwicklungskopie aktivieren. Die Snapshots enthalten auch uncommittete Änderungen; lokale Tests benötigen keinen Commit, Push oder PR. Pro Branch wird kein zusätzlicher Marketplace angelegt.

| Option | Wirkung |
| --- | --- |
| `DRY_RUN=1` | Schreibt Snapshots und zeigt die Befehle, ohne den Host aufzurufen. |
| `MARKETPLACE=../anderer-katalog` | Überschreibt aus einem Plugin heraus den lokalen Standard nur für diesen Aufruf. |

Frühere `plugin-manager-dev`-Installationen werden nicht automatisch entfernt. Nach erfolgreicher Gegenprobe alte Kopien deaktivieren oder entfernen. Eine CLI-Installation belegt keine automatische Synchronisierung mit einer Desktop-/Web-Kontooberfläche.

<a id="plugin-testen"></a>

#### Testen

**Im Chat:** Das Plugin-Projekt öffnen und zwischen Strukturprüfung, Tests und fachlichem Review unterscheiden:

> Synchronisiere die Plugin-Metadaten und prüfe sie. Führe verify für dieses Plugin und anschließend die regulären Tests aus. Berichte die Ergebnisse getrennt.

Für einen fachlichen Review zusätzlich: „Führe mit verify einen Zielbild-/Source-Review gegen die bestätigte SCOPE.md durch.“ Native Host-Tests oder Modelltests ausdrücklich separat beauftragen und den Host nennen. In Claude Code startet `/plugin-manager:verify` nur die lesende Prüfung; Tests benötigen einen zusätzlichen Auftrag.

**Im Terminal** – im Plugin-Repository:

```sh
make sync-plugin
make check-plugin
make verify
make test
```

`make verify` erkennt den Repository-Typ und liest Struktur sowie verfügbare lokale Zuordnungen. Es führt weder Tests noch Reparaturen oder Zielskripte aus. Aus `ai.plugins` kann ein separates Plugin explizit geprüft werden:

```sh
make verify SOURCE=../mein-plugin
```

| Prüfung | Aufruf | Aussage |
| --- | --- | --- |
| Unit-, Integrations- und Vertragstests | `make test` | Prüft implementierte Funktionen, Werkzeugabläufe und Verträge. |
| Native Host-Tests, sofern vorhanden | `make test-native` | Prüft lokale Installation und Aktualisierung mit isolierten Host-Profilen. |
| Modelltests, sofern eingerichtet | `make test-behavior` | Prüft Verhalten mit echten Modellaufrufen; kann Credits verbrauchen. |
| Zielbild-/Source-Review | `make verify REVIEW=1` und anschließender Agenten-Review | Sammelt statische Belege für den Vergleich mit bestätigten Anforderungen; führt keine Tests aus. |

Native Tests und Modelltests werden separat gestartet. Fehlende Suiten melden `NOT RUN`; das gilt nicht als bestandene Prüfung. Im Manager lassen sich Modelltests ausdrücklich mit `make test-behavior CLI=claude` oder `CLI=codex` starten. Die [Testübersicht](tests/README.md) erläutert Testarten und verfügbare Suiten.

Nach den automatisierten Prüfungen das Plugin in einer neuen Host-Sitzung fachlich testen. Die spätere Installation aus dem veröffentlichten Marketplace bleibt eine eigene Abnahme.

<a id="plugin-dokumentation"></a>

#### Dokumentation

Nach fachlichen Änderungen die Plugin-Dokumentation aktualisieren.

**Im Chat**

1. Das Plugin-Projekt öffnen.
2. Den Plugin-Ordner als Arbeitsordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `update` wählen oder in Claude Code `/plugin-manager:update` aufrufen.

Auftrag: „Führe update für mein-plugin aus. Aktualisiere die Dokumentation anhand der aktuellen Quellen und prüfe anschließend.“ Create liefert das Grundgerüst; die Inhalte müssen aus den tatsächlichen Funktionen vervollständigt werden.

Die gespeicherte Sprachwahl in `docs/documentation.json` steuert README und Anleitungen. Beim Manager sind Deutsch und Englisch mit Deutsch als Standard konfiguriert. Für dessen Dokumentationsprüfung:

```sh
make -C plugins/plugin-manager validate-docs OUTPUT=.
```

Bei anderen Plugins den dort dokumentierten Validator verwenden. Struktur- und Linkprüfung durch einen inhaltlichen Abgleich ergänzen. `update` pflegt Dokumentation; `install-local` erneuert installierte Entwicklungssnapshots. Keine der beiden Aktionen veröffentlicht Änderungen. [Manager-Entwicklerdokumentation](plugins/plugin-manager/docs/de/development.md).

<a id="plugin-veroeffentlichen"></a>

#### Veröffentlichen

Vor der Veröffentlichung Implementierung, Tests und Dokumentation im Plugin-Repository abschließen.

**Im Chat**

1. Das Plugin-Projekt öffnen.
2. Den Plugin-Ordner als Arbeitsordner auswählen.
3. Einen neuen Chat mit verfügbarem Plugin Manager starten.
4. `publish` wählen oder in Claude Code `/plugin-manager:publish` aufrufen.
5. Den Auftrag formulieren: „Bereite mit publish die Veröffentlichung dieses Plugins vor und lege mir den konkreten Plan zur Freigabe vor.“
6. Nach Freigabe den Ablauf über Feature-Branch, Commit, Push, PR, Checks und Merge ausführen.
7. Falls der Marketplace-Eintrag neu oder geändert ist, anschließend den [Marketplace veröffentlichen](#marketplace-veroeffentlichen).
8. Im Host den Marketplace synchronisieren, eine neue Sitzung öffnen und die veröffentlichte Plugin-Version fachlich prüfen.

Plugin-Quellen werden vor dem Marketplace-Eintrag veröffentlicht. Für die Repository-Installation sind keine Plugin-ZIPs oder Tags erforderlich. Details zu Freigabe, Checks und Wiederaufnahme stehen in der [Publish-Anleitung](plugins/plugin-manager/docs/de/publish.md).

## Migration

Der Arbeitsstand aus `zyris.skill.manager` wurde einschließlich uncommitteter Änderungen nach `plugins/plugin-manager` übernommen. Dieses Repository ist die kanonische Quelle; das alte lokale Repository bleibt als Sicherung erhalten und wird nicht parallel weitergepflegt. Seine Git-Historie und persönlichen IDE-Einstellungen wurden nicht kopiert.

Die technische Plugin-Identität lautet jetzt `plugin-manager`. Bestehende Installationen werden nicht automatisch umbenannt. Den neuen Eintrag installieren und nach erfolgreicher Prüfung die alte Kopie deaktivieren. Die Bestätigung des früheren Imports ist kein Abnahmetest dieses Marketplaces.
