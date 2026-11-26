# ⚡ Installation

[Deutsch](../de/installation.md) | **English**

[Home](../../README.en.md) · [Installation](installation.md) · [Concepts](concepts.md) · [Development](development.md)

Here you add the marketplace. That installs no plugin yet: it only gives you the possibility to install the plugins of this marketplace. Which ones they are is listed on the [start page](../../README.en.md). Account access, repository permissions and your organisation's policies apply. Menu labels are those of the app and may differ.

## Claude

### Claude Desktop App

1. Open **Einstellungen**.
2. Scroll to **Anpassungen** and select **Plugins**.
3. Select **+ Hinzufügen → Marketplace hinzufügen**, then **Aus einem Repository hinzufügen**.
4. Enter `https://github.com/draftm0de/ai.plugins` and select **Synchronisieren**.

The `/plugin` commands in the desktop app only open the plugin settings. Use this path.

### Claude CLI

In a terminal session started with `claude`:

```text
/plugin marketplace add https://github.com/draftm0de/ai.plugins
```

## Codex

### ChatGPT Desktop App

1. Open the **user icon** and select **Settings**.
2. Select **Integration → Plugins**.
3. Select **+ Add → A Marketplace** and enter `https://github.com/draftm0de/ai.plugins`.

### Codex CLI

```sh
codex plugin marketplace add https://github.com/draftm0de/ai.plugins
```

### ChatGPT Workspace

As a workspace administrator:

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
```

Codex:

```sh
codex plugin marketplace upgrade draftmode-ai-plugins
```

In the desktop apps you update in the plugin settings. Open a new chat afterwards.

## Remove

Claude (terminal):

```sh
claude plugin marketplace remove draftmode-ai-plugins
```

Codex:

```sh
codex plugin marketplace remove draftmode-ai-plugins
```

In the desktop apps you remove the marketplace in the plugin settings.

<hr>

This page is created automatically by `/plugin-manager:docs`. Do not edit it by hand.
