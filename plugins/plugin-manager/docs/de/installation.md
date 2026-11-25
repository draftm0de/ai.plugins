# Installation

**Deutsch** | [English](../en/installation.md)

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Start](../../README.md) · [Installation](installation.md) · [Skills](skills.md) · [Begriffe](concepts.md)

Du fügst den Marketplace einmal hinzu und installierst daraus Plugin Manager. Zugang, Repository-Berechtigungen und die Richtlinien deiner Organisation gelten. Die Menübezeichnungen entsprechen der jeweiligen App und können abweichen.

## Claude

### Desktop

1. Öffne **Einstellungen**.
2. Scrolle zu **Anpassungen** und wähle **Plugins**.
3. Wähle **+ Hinzufügen → Marketplace hinzufügen** und dann **Aus einem Repository hinzufügen**.
4. Gib `https://github.com/draftm0de/ai.plugins` ein und wähle **Synchronisieren**.
5. Wähle Plugin Manager im Marketplace und installiere es.

Die `/plugin`-Befehle führen in der Desktop-App nur zu den Plugin-Einstellungen. Nutze deshalb diesen Weg.

### CLI

In einer mit `claude` gestarteten Sitzung im Terminal:

```text
/plugin marketplace add https://github.com/draftm0de/ai.plugins
/plugin install plugin-manager@draftmode-ai-plugins
```

## Codex

### Desktop

1. Öffne das **Nutzer-Icon** und wähle **Settings**.
2. Wähle **Integration → Plugins**.
3. Wähle **+ Add → A Marketplace** und gib `https://github.com/draftm0de/ai.plugins` ein.
4. Wähle Plugin Manager und installiere es.

### CLI

```sh
codex plugin marketplace add https://github.com/draftm0de/ai.plugins
codex plugin add plugin-manager@draftmode-ai-plugins
```

Öffne danach einen neuen Chat.

### ChatGPT (Administrator eines Workspace)

1. Öffne **Admin → Plugins**.
2. Wähle **Add → Import marketplace**.
3. Gib `https://github.com/draftm0de/ai.plugins` als Repository-URL ein.
4. Lasse **Path** und **Branch/Tag/Commit** leer, um den Repository-Root auf dem Standardbranch zu verwenden.
5. Starte den Import und prüfe das Ergebnis.

Dieser Admin-Weg ist keine Behauptung identischer Menüs in jeder ChatGPT-Oberfläche. Kein Plugin-ZIP erforderlich.

## Aktualisieren

Claude (Terminal):

```sh
claude plugin marketplace update draftmode-ai-plugins
claude plugin update plugin-manager@draftmode-ai-plugins
```

Codex:

```sh
codex plugin marketplace upgrade draftmode-ai-plugins
```

In den Desktop-Apps aktualisierst du in den Plugin-Einstellungen. Öffne danach einen neuen Chat.

## Entfernen

Claude (Terminal):

```sh
claude plugin uninstall plugin-manager@draftmode-ai-plugins
```

Codex:

```sh
codex plugin remove plugin-manager@draftmode-ai-plugins
```

In den Desktop-Apps entfernst du das Plugin in den Plugin-Einstellungen.

---

Dokumentation mit Plugin Manager erstellt. Die Rechte am Quellprodukt bleiben unverändert.
