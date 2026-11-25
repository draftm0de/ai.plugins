# Development

[Installation](installation.md) · [Plugins](plugins.md) · [Concepts](concepts.md)

For people who work on this marketplace. You do not need this page to use it.

## Requirements

- Git and Python 3.10 or newer. Make is optional.
- Claude or Codex with the Plugin Manager installed.
- For a local installation the CLI of the host (`claude` or `codex`).
- One GitHub repository for the marketplace and one per plugin, each cloned locally.

## Set up

1. Create the marketplace repository on GitHub and clone it.
2. Run `/plugin-manager:setup` in it and choose "Marketplace".
3. Create and clone a plugin repository, run `/plugin-manager:setup` in it, choose "Plugin" and name this marketplace. This writes the entry in `marketplace.json` and the local association.

## Test locally

In the marketplace folder:

```bash
make install-local TARGET=claude
```

This installs the local state of every listed plugin as a separate development marketplace `<name>-dev`, uncommitted changes included. Open a new session afterwards. For Codex use `TARGET=codex`.

## Commands

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
| `python3 -B scripts/verify.py --source . --kind marketplace` | catalog or structure are invalid, `SCOPE.md` or `AGENTS.md` differ, or the documentation lacks pages, headings or link targets |

Your own steps belong into another file under `.github/workflows/`. Locally you check the same with `make test check verify`.

## Shared files

Plugin Manager keeps some files up to date (synced) and creates others only once (seed). `.project/plugins/plugin-manager/skeleton.json` lists the synced files. Do not change them: your own rules belong into `CUSTOM.AGENTS.md`, your own commands into `CUSTOM.mk`, your own CI steps into another file under `.github/workflows/`. If you change a synced file anyway, `/plugin-manager:setup` asks whether to keep it or adopt the template. If you keep `AGENTS.md`, the `SCOPE.md` of a marketplace or a standard under `docs/standards/`, `verify` fails.

## Publish

Commit and push the plugins first, then the marketplace:

```bash
make sync
```

```bash
make check test verify
```

Hosts install what lies on the default branch. There are no versions, tags or releases. People who already use the marketplace update it as described under [Installation](installation.md).
