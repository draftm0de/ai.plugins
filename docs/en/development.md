# Development

[Deutsch](../de/development.md) | **English**

[Home](../../README.en.md) · [Installation](installation.md) · [Concepts](concepts.md) · [Development](development.md)

For people who work on this marketplace. You do not need this page to use it.

## Requirements

- Git and Python 3.10 or newer. Make is optional.
- Claude or Codex with the Plugin Manager installed.
- For a local installation the CLI of the host (`claude` or `codex`).
- One GitHub repository for the marketplace and one per plugin, each cloned locally.

## Set up

### Marketplace

A marketplace is a repository of its own. Create it on GitHub, clone it and open the folder. Call `/plugin-manager:setup` there and choose "Marketplace". Among other things it asks for the name and the owner. After that the catalog `marketplace.json` and the shared files are in your repository.

### Adding plugins

Every plugin gets its own repository. Create it, clone it, open the folder and call `/plugin-manager:setup`. Choose "Plugin" and name the folder of this marketplace.

This writes the entry in `marketplace.json` and the local association with which you test the plugins on your machine later. You commit and push yourself, in both repositories.

If the plugin already exists, open its folder, call `/plugin-manager:setup` and ask to connect it with this marketplace. A plugin always belongs to exactly one marketplace.

## Test locally

The marketplace is the place Claude and Codex install from; the plugins themselves live in repositories of their own. For testing it builds a separate development marketplace `<name>-dev` from the folders on your machine and installs from it. Where the plugins lie is recorded in the local association that `:setup` creates. If the folder of a listed plugin is missing, it stops before it installs anything.

You need just one command, in the folder of the marketplace:

```bash
make install-local TARGET=claude
```

For Codex use `TARGET=codex`. With `DRY_RUN=1` it only builds the packages and installs nothing. Open a new session afterwards. Uncommitted changes are included. You do not have to generate or check anything first; you do that before you publish.

## Commands

`marketplace.json` is the one file you maintain: the name of the marketplace and the list of its plugins. Claude and Codex each read a **host catalog** of their own, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. Both are generated from `marketplace.json`; you never edit them by hand.

All commands run in the root of the repository. `make help` lists them too.

| Command | Purpose | Variables |
| --- | --- | --- |
| `make sync` | Generate the host catalogs from `marketplace.json` | |
| `make check` | Check that the host catalogs match | |
| `make test` | Deterministic tests | `TEST_GROUP=<name>`: one component only |
| `make verify` | Read-only structure check | `SOURCE=<folder>`; `REVIEW=1`: also compare with `SCOPE.md` |
| `make install-local` | Install the local plugin checkouts | `TARGET=claude` or `codex`; `DRY_RUN=1`: build the packages only |
| `make help` | Show the commands | |

Your own commands belong into `CUSTOM.mk`.

## CI

`.github/workflows/dm-verify.yml` runs on every push, every pull request and on demand. The run fails when a step fails.

| Step | Fails when |
| --- | --- |
| `python3 -B scripts/run_tests.py` | a test fails |
| `python3 -B scripts/marketplace.py check` | the host catalogs do not match `marketplace.json` |
| `python3 -B scripts/verify/structure.py --source .` | manifests, catalogs, skills or the structure are invalid |
| `python3 -B scripts/verify/standards.py --source .` | `SCOPE.md` or `AGENTS.md` differ |
| `python3 -B scripts/verify/docs.py --source .` | never: missing pages, headings or link targets of the documentation are only warnings |

Your own steps belong into another file under `.github/workflows/`. Locally you check the same with `make test check verify`.

## Publish

Commit and push the plugins first, then the marketplace:

```bash
make sync
```

```bash
make check test verify
```

Hosts install what lies on the default branch. There are no versions, tags or releases. People who already use the marketplace update it as described under [Installation](installation.md).

<hr>

This page is created automatically by `/plugin-manager:docs`. Do not edit it by hand.
