# Plugin Manager

[Deutsch](README.md) | **English**

<img src="docs/assets/zyris-icon.png" alt="ZYRIS" width="48">

## Who it is for

For developers and teams maintaining skills as installable plugins. The Manager supports structure, documentation, validation and publication through a checked GitHub PR.

## What it looks like

[Examples and existing Claude dialogs](docs/en/screens.md) show usage. Earlier import confirmations do not certify the new create/configure workflows.

## Capabilities and modes

**marketplace-create** configures a cloned marketplace. **plugin-create** creates and associates a separate plugin. **configure** connects an existing plugin to a marketplace. **plugin-verify**, **marketplace-verify** and **verify** are read-only. **update** maintains documentation and **publish** prepares separate approval-gated publications. `init` is unsupported. [Workflows](docs/en/usage.md).

The six skills are `marketplace-create`, `plugin-create`, `configure`, `verify`, `update` and `publish`. `plugin-manager` names the plugin only. Shared rules and tools live in [`skills/_shared/`](skills/_shared/WORKFLOWS.md), without an additional skill. Explicit verify variants remain commands; init is unsupported.

## Quick start

Add `https://github.com/draftm0de/ai.plugins` as a marketplace in plugin settings and install **Plugin Manager**. No ZIP or tag is needed. [Installation paths](docs/en/installation.md).

## Usage

Select the plugin and ask: “Verify this repository.” For documentation: “Update the documentation in German and English.” Claude Code also supports `/plugin-manager:verify PATH` and the other action commands. [Usage](docs/en/usage.md).

`update` is the skill entry point for **update**. It refreshes maintained Markdown from current sources and templates; README is not automatically regenerated on every build. [Maintain documentation](docs/en/development.md#maintain-documentation).

## Storage and privacy

The Manager writes documentation and, for plugin-create, a separate plugin skeleton. Publication journals stay outside the source and plugin installation. Private data, credentials and unrelated changes are excluded. Your AI host processes supplied sources under its own terms.

## Project status

The user confirms Manager and Coach are present in the published marketplace. Earlier Claude/GPT import confirmations concern that earlier state; current Manager extensions remain local. Isolated CLI tests are documented separately. This does not certify every feature, automatic updates or the entire publication workflow. License: [MIT](LICENSE). [Evidence](docs/en/release-evidence.md).

## Development

`plugin-create --skeleton` creates only a new scaffold without domain content. Skill import is not offered. The skeleton includes a pending `SCOPE.md` and development rules. `verify` offers an explicit read-only scope/source review: static evidence checks with `REVIEW=1`, followed by semantic comparison by the agent. No automatic repairs or test execution. [Workflow and limits](docs/en/usage.md).

The [test guide](tests/README.md) describes the shared layout by test type. `make test` runs unit, integration and contract tests; native host and model tests are started separately.

```sh
make sync-plugin
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

`make sync-plugin` generates host metadata to commit. `make install-local` and `make update-local` test local edits without a commit or push; the **update** skill action maintains documentation. [Development](docs/en/development.md).

Documentation prepared with Plugin Manager.
