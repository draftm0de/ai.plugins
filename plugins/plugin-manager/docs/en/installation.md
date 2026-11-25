# Installation

[Deutsch](../de/installation.md) | **English**

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Home](../../README.en.md) · [Installation](installation.md) · [Skills](skills.md) · [Concepts](concepts.md)

You add the marketplace once and install Plugin Manager from it. Account access, repository permissions and your organisation's policies apply. Menu labels are those of the app and may differ.

## Claude

### Desktop

The labels below are those of the German interface of the desktop app.

1. Open **Einstellungen** (settings).
2. Scroll to **Anpassungen** and select **Plugins**.
3. Select **+ Hinzufügen → Marketplace hinzufügen**, then **Aus einem Repository hinzufügen**.
4. Enter `https://github.com/draftm0de/ai.plugins` and select **Synchronisieren**.
5. Select Plugin Manager in the marketplace and install it.

The `/plugin` commands only open the plugin settings in the desktop app, so use this path there.

### CLI

In a terminal session started with `claude`:

```text
/plugin marketplace add https://github.com/draftm0de/ai.plugins
/plugin install plugin-manager@draftmode-ai-plugins
```

## Codex

### Desktop

1. Open the **user icon** and select **Settings**.
2. Select **Integration → Plugins**.
3. Select **+ Add → A Marketplace** and enter `https://github.com/draftm0de/ai.plugins`.
4. Select Plugin Manager and install it.

### CLI

```sh
codex plugin marketplace add https://github.com/draftm0de/ai.plugins
codex plugin add plugin-manager@draftmode-ai-plugins
```

Then open a new chat.

### ChatGPT (workspace administrator)

1. Open **Admin → Plugins**.
2. Select **Add → Import marketplace**.
3. Enter `https://github.com/draftm0de/ai.plugins` as the repository URL.
4. Leave **Path** and **Branch/Tag/Commit** empty to use the repository root on the default branch.
5. Start the import and review the result.

This admin path does not imply identical menus in every ChatGPT interface. No plugin ZIP is required.

## Update

Claude (terminal):

```sh
claude plugin marketplace update draftmode-ai-plugins
claude plugin update plugin-manager@draftmode-ai-plugins
```

Codex:

```sh
codex plugin marketplace upgrade draftmode-ai-plugins
```

In the desktop apps update in the plugin settings, then open a new chat.

## Remove

Claude (terminal):

```sh
claude plugin uninstall plugin-manager@draftmode-ai-plugins
```

Codex:

```sh
codex plugin remove plugin-manager@draftmode-ai-plugins
```

In the desktop apps remove the plugin in the plugin settings.

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.
