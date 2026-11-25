# Installation

[Deutsch](../de/installation.md) | **English**

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Home](../../README.en.md) · [Installation](installation.md) · [Plugins](plugins.md) · [Concepts](concepts.md)

You add the marketplace once and install the plugin you want from it. Account access, repository permissions and your organisation's policies apply. Menu labels are those of the app and may differ.

## Claude

### Desktop

The labels below are those of the German interface of the desktop app.

1. Open **Einstellungen** (settings).
2. Scroll to **Anpassungen** and select **Plugins**.
3. Select **+ Hinzufügen → Marketplace hinzufügen**, then **Aus einem Repository hinzufügen**.
4. Enter `https://github.com/draftm0de/ai.plugins` and select **Synchronisieren**.
5. Select the plugin you want in the marketplace and install it.

The `/plugin` commands only open the plugin settings in the desktop app, so use this path there.

### CLI

In a terminal session started with `claude`:

```text
/plugin marketplace add https://github.com/draftm0de/ai.plugins
/plugin install <plugin>@draftmode-ai-plugins
```

## Codex

### Desktop

1. Open the **user icon** and select **Settings**.
2. Select **Integration → Plugins**.
3. Select **+ Add → A Marketplace** and enter `https://github.com/draftm0de/ai.plugins`.
4. Select the plugin you want and install it.

### CLI

```sh
codex plugin marketplace add https://github.com/draftm0de/ai.plugins
codex plugin add <plugin>@draftmode-ai-plugins
```

Then open a new chat.

## Update

Claude (terminal):

```sh
claude plugin marketplace update draftmode-ai-plugins
claude plugin update <plugin>@draftmode-ai-plugins
```

Codex:

```sh
codex plugin marketplace upgrade draftmode-ai-plugins
```

In the desktop apps update in the plugin settings, then open a new chat.

## Remove

Claude (terminal):

```sh
claude plugin uninstall <plugin>@draftmode-ai-plugins
```

Codex:

```sh
codex plugin remove <plugin>@draftmode-ai-plugins
```

In the desktop apps remove the plugin in the plugin settings.

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.
