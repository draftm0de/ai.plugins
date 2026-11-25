# Installation

**Deutsch** | [English](../en/installation.md)

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Start](../../README.md) · [Installation](installation.md) · [Plugins](plugins.md) · [Begriffe](concepts.md)

Du fügst den Marketplace einmal hinzu und installierst daraus {{PLUGIN_LABEL}}. Zugang, Repository-Berechtigungen und die Richtlinien deiner Organisation gelten. Die Menübezeichnungen entsprechen der jeweiligen App und können abweichen.

## Claude

### Desktop

1. Öffne **Einstellungen**.
2. Scrolle zu **Anpassungen** und wähle **Plugins**.
3. Wähle **+ Hinzufügen → Marketplace hinzufügen** und dann **Aus einem Repository hinzufügen**.
4. Gib `{{MARKETPLACE_URL}}` ein und wähle **Synchronisieren**.
5. Wähle {{PLUGIN_LABEL}} im Marketplace und installiere es.

Die `/plugin`-Befehle führen in der Desktop-App nur zu den Plugin-Einstellungen. Nutze deshalb diesen Weg.

### CLI

In einer mit `claude` gestarteten Sitzung im Terminal:

```text
/plugin marketplace add {{MARKETPLACE_URL}}
/plugin install {{PLUGIN_ID}}
```

## Codex

### Desktop

1. Öffne das **Nutzer-Icon** und wähle **Settings**.
2. Wähle **Integration → Plugins**.
3. Wähle **+ Add → A Marketplace** und gib `{{MARKETPLACE_URL}}` ein.
4. Wähle {{PLUGIN_LABEL}} und installiere es.

### CLI

```sh
codex plugin marketplace add {{MARKETPLACE_URL}}
codex plugin add {{PLUGIN_ID}}
```

Öffne danach einen neuen Chat.

## Aktualisieren

Claude (Terminal):

```sh
claude plugin marketplace update {{MARKETPLACE_NAME}}
claude plugin update {{PLUGIN_ID}}
```

Codex:

```sh
codex plugin marketplace upgrade {{MARKETPLACE_NAME}}
```

In den Desktop-Apps aktualisierst du in den Plugin-Einstellungen. Öffne danach einen neuen Chat.

## Entfernen

Claude (Terminal):

```sh
claude plugin uninstall {{PLUGIN_ID}}
```

Codex:

```sh
codex plugin remove {{PLUGIN_ID}}
```

In den Desktop-Apps entfernst du das Plugin in den Plugin-Einstellungen.

---

Dokumentation mit Plugin Manager erstellt. Die Rechte am Quellprodukt bleiben unverändert.
