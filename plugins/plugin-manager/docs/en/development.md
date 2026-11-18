# Development

[Deutsch](../de/development.md) | **English**

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.en.md) · [Guides](README.md)

## Source of truth

`skills/plugin-manager/` contains rules, runtime and canonical templates. Root `plugin.json` owns identity and host metadata. `make sync-plugin` derives the three committed host files; `make check-plugin` detects drift without writing. Capabilities stay under `skills/`, assets under `assets/`.

## Checks

```sh
make check-plugin
make test
make verify SOURCE=.
make validate-docs OUTPUT=.
```

Verify never executes target code. It checks neutral skill paths, versionless import metadata, template copies, ignore rules, static Python imports and documentation pointers. Product behavior tests and host acceptance remain necessary.

## Packaging

### Develop locally

Run these commands from the repository. Python 3, Make and the selected host CLI (`claude` or `codex`) must be available.

1. Install the current working tree locally once:

   ```sh
   make install-local TARGET=claude
   # Alternatively for Codex:
   make install-local TARGET=codex
   ```

2. Apply your working-tree edits:

   ```sh
   make update-local TARGET=claude
   # Alternatively for Codex:
   make update-local TARGET=codex
   ```

3. Open a new local session and verify the change. Enable only the intended remote or development copy to avoid duplicate skill names.

These commands create a filtered snapshot under `dist/local-development/` and register it through the host CLI as a separate `plugin-manager-dev` marketplace. Uncommitted edits are included; no commit, push or ZIP is needed. The generated content hash is only a local cache identifier and is never written to the source manifest. Keep the checkout and snapshot available while using the installation.

With `DRY_RUN=1`, the snapshot is created and commands are displayed without invoking the host CLI. Example: `make install-local TARGET=codex DRY_RUN=1`. This does not change installed plugins.

This workflow covers local Claude Code and Codex installations. Import through a desktop or web account interface remains separate; synchronization to that interface is not established by these commands. Do not manually copy files into `~/.claude/plugins/cache`: the host CLI manages registration and caching. Our tests do not modify personal installations; native integration tests use temporary profiles.

### Metadata and export

`make sync-plugin` updates host manifests from `plugin.json`; `make check-plugin` validates them without changes. All four plugin commands live directly in the `Makefile`. `install.sh` is an optional forwarding wrapper, for example `bash install.sh install-local --target claude`; it has no default action.

Regular repository imports use [plugin settings](installation.md). Plugin ZIP building and the old `package`, `install` and `update` Make targets are removed. The **update** skill action for documentation remains available. The separate website export remains available through `make check-docs-export` and `make export-docs`.

## CI and releases

The [CI](../../.github/workflows/validate.yml) checks tests, repository metadata and documentation. It publishes nothing. Publish ends at the checked GitHub merge; there are no release Actions, tags or catalog promotion. [Workflow](publish.md) · [Evidence](release-evidence.md).

## Maintain documentation

Update maintains configured languages from current sources. Example: `make init-plugin SOURCE=... OUTPUT=... LANGUAGES="de en" DEFAULT_LANGUAGE=de`. Optional: `PLUGIN_NAME=my-plugin REPOSITORY=https://github.com/OWNER/REPO AUTHOR="Confirmed publisher"`. Init creates a separate empty project; the agent then completes its documentation. Website export retains its [contract](../../skills/plugin-manager/references/export-contract.md).

Init uses a confirmed plugin name for `plugin.json` and both marketplace catalogs; local development appends `-dev`. If the name is missing or unclear, the agent asks before initialization. `PLUGIN_NAME` may differ from the bundled skill name; its folder and frontmatter remain unchanged. Without the parameter, the helper defaults to the source skill name.

This plugin lives under `plugins/plugin-manager/` in `ai.plugins`. The shared marketplace is `draftmode-ai-plugins`; its catalogs live at the repository root. This plugin has no separate committed marketplace. Commands above run from the plugin folder; the root Makefile forwards the main checks and local installation commands.
