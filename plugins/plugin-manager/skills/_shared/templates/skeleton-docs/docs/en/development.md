# Development

[Deutsch](../de/development.md) | **English**

[Home](../../README.en.md) · [Overview](README.md) · [Install](installation.md) · [Use](usage.md) · [Screens](screens.md) · [FAQ](faq.md)

## Source of truth

<!-- Root plugin.json owns identity; sync-plugin derives only host plugin manifests. Separate marketplaces own catalogs. Keep skills/ at root and omit manifest versions. -->

<!-- Management tools require Git and Python 3.10+; Make is only a convenience wrapper. Management needs the selected host CLI only for automatic local installation/updates; explicitly requested model tests also need an authenticated CLI. Publish uses a sufficiently capable GitHub connector or alternatively authenticated gh; no GitLab MRs. First verify remote read, push, PR create/read, checks, rules and controlled merge capabilities and permissions. Report missing capabilities specifically; never install tools automatically. No additional Python packages, release Actions or version/tag requirements. See ../prerequisites.md in generated projects. -->

Read [SCOPE.md](../../SCOPE.md), [AGENTS.md](../../AGENTS.md) and [architecture](../architecture.md). Runtime belongs under skills/; root scripts/ contains development tools.

## Checks

<!-- Evaluate effective .local/marketplace.json ignore rules with Git before writing mappings; conflicting negations abort without changing existing files. -->

make verify checks structure; make verify REVIEW=1 collects source-review evidence. make test runs the configured deterministic tests as a separate development step. These commands have not been run merely by creating this skeleton.

## Packaging

<!-- Explain Makefile install-local TARGET=claude|codex, separate <marketplace-name>-dev snapshots under dist/local-development, uncommitted edits, DRY_RUN=1 creating snapshots without host calls, CLI prerequisites and local-vs-account scope. Keep matching numbered/code-block formatting across hosts and languages. Explain check-plugin/sync-plugin. No plugin ZIP builder or remote install/update targets. Never recommend copying into host caches. -->

<!-- Local snapshots read the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. Local tests require no commit, push or PR. Keep one shared `<marketplace-id>-dev`, with no additional marketplaces per branch. `configure` is the normal setup path. `local-marketplace.example.json` is an optional manual copy template. Only `.local/marketplace.json` is read for local runtime mappings; never commit those mappings. -->

make sync-plugin derives host metadata; make check-plugin checks drift. The plugin owns no marketplace catalogs.

## CI and releases

<!-- CI validates only. Publish: reviewed diff/message, approval, commit, push, PR, checks/reviews, merge. Separate plugin and marketplace plans; publish new plugin sources first. PRs require an observed base commit. An empty remote/unborn HEAD requires separately approved initial commit and direct push, never automatic initialization. No tags or releases. -->

The starter CI runs make test and make check-plugin. Its existence is not evidence of a successful run. Creation does not commit, push or publish.

## Maintain documentation

Update the configured documentation languages from confirmed scope and actual source as implementation progresses. Replace skeleton claims only when supported by evidence.

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.

Test layers: `make test` (unit, integration, contracts), `make test-unit`, `make test-integration`, `make test-contracts`; explicit `make test-native` / `make test-behavior`. Missing suites report `NOT RUN`. See `tests/README.md`.
