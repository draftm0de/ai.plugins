# Installation

[Deutsch](../de/installation.md) | **English**

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Home](../../README.en.md) · [Installation](installation.md) · [Skills](skills.md) · [Concepts](concepts.md)

You add the marketplace once and install {{PLUGIN_LABEL}} from it. Account access, repository permissions and your organisation's policies apply. Menu labels are those of the app and may differ.

## Claude

### Desktop

The labels below are those of the German interface of the desktop app.

1. Open **Einstellungen** (settings).
2. Scroll to **Anpassungen** and select **Plugins**.
3. Select **+ Hinzufügen → Marketplace hinzufügen**, then **Aus einem Repository hinzufügen**.
4. Enter `{{MARKETPLACE_URL}}` and select **Synchronisieren**.
5. Select {{PLUGIN_LABEL}} in the marketplace and install it.

The `/plugin` commands only open the plugin settings in the desktop app, so use this path there.

### CLI

In a terminal session started with `claude`:

```text
/plugin marketplace add {{MARKETPLACE_URL}}
/plugin install {{PLUGIN_ID}}
```

## Codex

### Desktop

1. Open the **user icon** and select **Settings**.
2. Select **Integration → Plugins**.
3. Select **+ Add → A Marketplace** and enter `{{MARKETPLACE_URL}}`.
4. Select {{PLUGIN_LABEL}} and install it.

### CLI

```sh
codex plugin marketplace add {{MARKETPLACE_URL}}
codex plugin add {{PLUGIN_ID}}
```

Then open a new chat.

## Update

Claude (terminal):

```sh
claude plugin marketplace update {{MARKETPLACE_NAME}}
claude plugin update {{PLUGIN_ID}}
```

Codex:

```sh
codex plugin marketplace upgrade {{MARKETPLACE_NAME}}
```

In the desktop apps update in the plugin settings, then open a new chat.

## Remove

Claude (terminal):

```sh
claude plugin uninstall {{PLUGIN_ID}}
```

Codex:

```sh
codex plugin remove {{PLUGIN_ID}}
```

In the desktop apps remove the plugin in the plugin settings.

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.
