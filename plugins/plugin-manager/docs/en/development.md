# Development

[Deutsch](../de/development.md) | **English**

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.en.md) · [Guides](README.md)

## Source of truth

The five public entry points live at `skills/<action-name>/SKILL.md`. Shared rules live in `skills/_shared/WORKFLOWS.md`, helpers in `skills/_shared/scripts/` and templates in `skills/_shared/templates/`. `_shared` has no SKILL.md and is not exposed as an additional skill. `docs/documentation.json` points to `skills/update` and lists shared sources and the other skills under `extra_sources`.

`skills/` is the host-neutral source. `plugin.json` owns plugin metadata; `marketplace.json` in a separate marketplace owns catalogs. Only the existing Manager in `ai.plugins/plugins/plugin-manager` remains embedded. New marketplaces need no Manager checkout. Canonical templates live under `skills/_shared/templates/plugin/` and `templates/marketplace/`, each split into `sync/` (kept in sync, hashed) and `seed/` (created once). `make build-skeleton-hashes` writes the hash files `skills/_shared/manifests/<kind>.sync.json`; `make check-skeleton-hashes` verifies them and runs in CI with exit 1 on drift.

Management tools require Git and Python 3.10+; Make is only a convenience wrapper. Management needs the selected host CLI only for automatic local installation/updates; explicitly requested model tests also need an authenticated CLI. Publish uses a sufficiently capable GitHub connector or alternatively authenticated gh; no GitLab MRs. First verify remote read, push, PR create/read, checks, rules and controlled merge capabilities and permissions. Report missing capabilities specifically; never install tools automatically. No additional Python packages, release Actions or version/tag requirements.

[Canonical prerequisites](../../skills/_shared/references/prerequisites.md)

## Checks

The shared [test layout](../../tests/README.md) groups by test type first: `unit/`, `integration/`, `contracts/`, and optional `behavior/` and `native/`. Skills or components sit underneath; data and helpers live in `fixtures/` and `support/`.

`make test` runs only unit, integration and contract tests. Individual layers: `make test-unit`, `make test-integration`, `make test-contracts`. `make test-native` and `make test-behavior` are requested separately. Absent suites explicitly report `NOT RUN`; native tests require explicit layer selection.

`make test` checks tooling and temporary repository workflows. `make verify` and `make verify SOURCE=...` only read structure and available local mappings. They run no target scripts or repairs. `make validate-docs OUTPUT=.` separately validates documentation.

Native acceptance: `make test-native` in the Manager directory. The workflow test uses fictional temporary repositories and isolated Claude/Codex profiles. It installs two separate plugins and checks loaded content after uncommitted edits. This does not replace GitHub/GUI acceptance.

## Packaging

Repository installation requires no plugin ZIPs or manifest versions. `make sync-plugin`/`check-plugin` handle plugin manifests; `make sync-marketplace`/`check-marketplace` handle host catalogs. Root `sync-plugin`/`check-plugin` aggregate targets in ai.plugins additionally handle the embedded Manager.

`make install-local TARGET=claude` or `TARGET=codex` creates filtered snapshots under `dist/local-development/` and installs all associated plugins as `<marketplace-id>-dev`. It needs no commit or push, and calling it again refreshes the snapshots. `DRY_RUN=1` writes snapshots without calling a host. Host caches are not directly edited; the CLI manages its installations.

Local paths stay Git-ignored: `sources` in `.local/marketplace.json` of the marketplace, and `marketplace_path` in `.project/plugins/plugin-manager/local.json` of a plugin. A plugin belongs to exactly one marketplace; there is no per-call override. All required checkouts must be available before installation.

Local snapshots read the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. Local tests require no commit, push or PR. Keep one shared `<marketplace-id>-dev`, with no additional marketplaces per branch.

The local association of a plugin with its one marketplace is set up and changed by `plugin-manager` (associate). The path of the marketplace checkout lives in the Git-ignored `.project/plugins/plugin-manager/local.json` of the plugin; the checkouts of the plugins live under `sources` in the Git-ignored `.local/marketplace.json` of the marketplace; never commit those mappings. `local-marketplace.example.json` is an optional manual copy template for the marketplace side.

Without Make in the marketplace:

```sh
python3 -B scripts/local_plugins.py install-local --target claude
```

## CI and releases

CI validates tests, metadata and documentation and publishes nothing. [Publish](publish.md) uses separate plans per repository. New plugin sources must be published and observed before the marketplace entry is published. No release Actions, tags or plugin ZIPs.

## Maintain documentation

The docs action rereads current sources and preserves the configured languages. `create --kind plugin` generates templates; the agent completes them from evidenced product behavior. No invented publisher, license or skill instructions. init is unsupported.

[Create/associate commands](../../skills/_shared/references/workflows.md)

For documentation, ask: “Run docs for this repository and validate afterward.” The agent rereads `docs/documentation.json`, skill, references, manifests and tools, then maintains `README.md`, `README.en.md`, `docs/de/` and `docs/en/`. Scaffold only creates missing files; existing content is deliberately revised. `make validate-docs OUTPUT=.` checks structure and local links. These checks do not replace content review or host testing.

New plugin and marketplace templates include SCOPE.md and shared development rules in AGENTS.md and docs/architecture.md; CLAUDE.md points to them. These are versioned target/structure rules. Existing content is preserved; domain requirements are never inferred from code. Review regressions in `tests/integration/verify/test_scope_review.py` test evidence boundaries, missing requirements, skeletons and incorrect runtime dependencies without executing target code. They do not establish LLM review reliability.

### Scope/source review model evaluations

From the Manager directory explicitly run `make test-behavior CLI=claude` or `CLI=codex`; `CASE=correct_consent` selects one case. [Scenarios, grading and limitations](../../tests/behavior/README.md). Both models receive complete fictional files and the same review rules, without expected answers. Tests cover correct implementations, real defects, test gaps, missing source and injected success claims. Automated grading is complemented by human review. No model calls in the normal suite; no installation or publication.

Format checks precede changes: no parallel host skill directories or marketplace key in distribution metadata. Unknown catalog entry fields are rejected before associate, never discarded. Documentation schema versions must be integers. Conflicting existing docs/architecture.md or docs/prerequisites.md block `create --kind plugin` without overwriting content.

`create --kind plugin` also rejects old host directories before changes. Skill import through `create --kind plugin` is unsupported; layout and documentation manifest checks remain in place.
