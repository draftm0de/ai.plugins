# Installation

**Deutsch** | [English](../en/installation.md)

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Start](../../README.md) · [Installation](installation.md) · [Skills](skills.md) · [Begriffe](concepts.md)

Du fügst den Marketplace einmal hinzu und installierst daraus den Plugin Manager. Zugang, Repository-Berechtigungen und Organisationsrichtlinien gelten. Die Menüschritte beruhen auf Angaben und Screenshots vom 18.11.2026.

## Claude

### Desktop

1. Öffne **Einstellungen**.
2. Scrolle zu **Anpassungen** und wähle **Plugins**.
3. Wähle **+ Hinzufügen → Marketplace hinzufügen**.
4. Wähle **Aus einem Repository hinzufügen**.
5. Gib `https://github.com/draftm0de/ai.plugins` unter **URL** ein und klicke **Synchronisieren**.
6. Wähle den Manager im Marketplace und installiere ihn.

In Claude Desktop 5.11492.5 öffneten beim Nutzer `/plugin install …` und `/plugin marketplace add …` lediglich **Einstellungen → Plugins**; der vollständige Auftrag wurde darüber nicht ausgeführt. Nutze deshalb auch im Reiter **Code** den oben beschriebenen UI-Weg. Das Öffnen der Verwaltung bestätigt keine Installation. Die genaue interne Ursache ist nicht abschließend belegt; Änderungen an der JSON-Einrückung helfen hier nicht.

Anthropic unterscheidet den Terminal-Befehl von der Desktop-Plugin-Verwaltung: [Desktop-Dokumentation](https://code.claude.com/docs/en/desktop#feature-comparison).

### CLI

Die folgenden Slash-Befehle gelten für eine mit `claude` gestartete Sitzung im Terminal. Sie sind keine Installationsanweisung für das Eingabefeld im Desktop-Code-Reiter.

1. Füge den Marketplace hinzu:

   ```text
   /plugin marketplace add https://github.com/draftm0de/ai.plugins
   ```

2. Öffne die Plugin-Details:

   ```text
   /plugin install plugin-manager@draftmode-ai-plugins
   ```

3. Wähle den Installationsbereich und bestätige die Installation.

[Offizielle Anleitung](https://code.claude.com/docs/en/discover-plugins#install-a-plugin).

## Codex

### Desktop

1. Öffne das **Nutzer-Icon** und wähle **Settings**.
2. Wähle **Integration → Plugins**.
3. Wähle **+ Add → A Marketplace**.
4. Gib `https://github.com/draftm0de/ai.plugins` als Repository-URL ein und bestätige das Hinzufügen.
5. Wähle **Plugin Manager** und installiere ihn.

### CLI

Die folgenden Befehle werden direkt in der Terminal-Shell ausgeführt.

1. Füge den Marketplace hinzu:

   ```sh
   codex plugin marketplace add https://github.com/draftm0de/ai.plugins
   ```

2. Installiere das Plugin:

   ```sh
   codex plugin add plugin-manager@draftmode-ai-plugins
   ```

3. Öffne einen neuen Codex-Chat und prüfe, ob das Plugin verfügbar ist.

### ChatGPT (Administrator eines Workspace)

1. Öffne **Admin → Plugins**.
2. Wähle **Add → Import marketplace**.
3. Gib `https://github.com/draftm0de/ai.plugins` als Repository-URL ein.
4. Lasse **Path** und **Branch/Tag/Commit** leer, um den Repository-Root auf dem Standardbranch zu verwenden.
5. Starte den Import und prüfe das Ergebnis.

Dieser Admin-Weg ist keine Behauptung identischer Menüs in jeder ChatGPT-Oberfläche. Kein Plugin-ZIP erforderlich.

## Aktualisieren

In Claude Desktop verwende die Plugin-Verwaltung zum Aktualisieren beziehungsweise Synchronisieren und öffne danach einen neuen Chat. Die folgenden Befehle sind nur die Alternative für Claude Code im Terminal:

```text
/plugin marketplace update draftmode-ai-plugins
/plugin update plugin-manager@draftmode-ai-plugins
```

In Codex:

```sh
codex plugin marketplace upgrade draftmode-ai-plugins
```

Die eingecheckten Manifeste enthalten keine Version. Claude Code verwendet dann den Commit als Update-Kennung. Codex aktualisiert beim Git-Marketplace-Upgrade die installierte Kopie; seine angezeigte interne Cache-Version kann trotzdem gleich bleiben. Ein Push allein belegt noch keine Aktualisierung in jedem Desktop-Konto. Ein vollständiger Update-Test ist getrennt vom erfolgreichen Erstimport zu prüfen.

## Entfernen

Entferne das Plugin in den Plugin-Einstellungen, im Terminal von Claude Code mit `/plugin uninstall plugin-manager@draftmode-ai-plugins` oder bei Codex mit `codex plugin remove plugin-manager@draftmode-ai-plugins`. Deine Projektdateien bleiben unverändert.

---

Dokumentation mit Plugin Manager erstellt.
