# Plugin Manager

[Deutsch](README.md) | **English**

<img src="docs/assets/zyris-icon.png" alt="ZYRIS" width="48">

## Who it is for

For developers and teams maintaining skills as installable plugins. The Manager supports structure, documentation, validation and publication through a checked GitHub PR.

## What it looks like

[Examples and existing Claude dialogs](docs/en/screens.md) show usage. Earlier import confirmations do not certify the new create/configure workflows.

## Capabilities and modes

**setup** (`/plugin-manager:setup`) configures a cloned marketplace or creates and associates a separate plugin, as guided flows; the skill checks the state, runs exactly the needed flow and may be called repeatedly. It changes the marketplace association of a plugin (exactly one marketplace) on request in the `associate` flow. **verify** is read-only and detects itself whether a plugin or a marketplace is present. **docs** maintains documentation and **publish** prepares separate approval-gated publications; both start only when the workpackage is ready and otherwise point to `setup`. `init` is unsupported. [Workflows](docs/en/usage.md).

The four skills are `setup`, `docs`, `verify` and `publish`. Shared rules and tools live in [`skills/_shared/`](skills/_shared/WORKFLOWS.md). The kind (plugin or marketplace) is never a call argument; init is unsupported.

## Quick start

Add `https://github.com/draftm0de/ai.plugins` as a marketplace in plugin settings and install **Plugin Manager**. No ZIP or tag is needed. [Installation paths](docs/en/installation.md).

## Usage

Select the plugin and ask: “Verify this repository.” For documentation: “Update the documentation in German and English.” Claude Code also supports `/plugin-manager:verify PATH` and the other action commands. [Usage](docs/en/usage.md).

`docs` is the skill entry point for **docs** (`/plugin-manager:docs`). It refreshes maintained Markdown from current sources and templates; README is not automatically regenerated on every build. [Maintain documentation](docs/en/development.md#maintain-documentation).

## Storage and privacy

The Manager writes documentation and, for `create --kind plugin`, a separate plugin skeleton. Publication journals stay outside the source and plugin installation. Private data, credentials and unrelated changes are excluded. Your AI host processes supplied sources under its own terms.

## Project status

The user confirms Manager and Coach are present in the published marketplace. Current Manager extensions remain local. This does not certify every feature, automatic updates or the entire publication workflow. License: [MIT](LICENSE).

## Development

`create --kind plugin --skeleton` creates only a new scaffold without domain content. Skill import is not offered. The skeleton includes a pending `SCOPE.md` and development rules. `verify` offers an explicit read-only scope/source review: static evidence checks with `REVIEW=1`, followed by semantic comparison by the agent. No automatic repairs or test execution. [Workflow and limits](docs/en/usage.md).

The [test guide](tests/README.md) describes the shared layout by test type. `make test` runs unit, integration and contract tests; native host and model tests are started separately.

```sh
make sync-plugin
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

`make sync-plugin` generates host metadata to commit. `make install-local` test local edits without a commit or push; the **docs** skill action maintains documentation. [Development](docs/en/development.md).

Documentation prepared with Plugin Manager.
