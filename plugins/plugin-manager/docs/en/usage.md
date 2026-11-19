# Usage

New skeleton pages are filled with the actual scaffold status in the selected languages and validated before writes. Existing prose is preserved. Final checks separately assess the actual plugin structure, marketplace and documentation. Errors in preserved pages remain visible; `checks.status=needs_attention` means creation still has outstanding findings. `passed` also checks technical consistency of licensing files and documentation; it does not establish legal suitability or functional acceptance. The completion report also states the licensing decision, actual license files and tests or host checks still pending.

[Deutsch](../de/usage.md) | **English**

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.en.md) · [Guides](README.md)

## Set up

Targets come from your open project or explicit input, never automatically from the Manager installation. Existing project facts and Git origin are reused; only missing or conflicting inputs need clarification. Display name and technical identifier are distinct. Publisher, license and skill behavior are never invented.

## Choose a workflow

In Claude Code use `/plugin-manager:marketplace-create`, `/plugin-manager:plugin-create` or `/plugin-manager:configure`. In Codex/GPT select the capability or describe the action. `init` is unsupported.

For `plugin-create`, questions and replies follow the language of your current message. A bare slash command retains the established conversation language; without language context, the agent briefly asks. Documentation languages are selected independently.

Missing inputs are collected in small steps using the host's structured question tool when available. Without language context, only the language choice is asked first; setup then continues in that language. Confirmed inputs are not asked again. If no question tool is available, the agent briefly explains that and asks one question at a time in chat.

For an existing plugin, an unknown conversation language is still resolved alone first. The only action choices are then “Verify” and “Configure”, with English-only descriptions. Repeated creation detects an existing product before license validation and leaves it unchanged.

Before creation, the agent resolves the licensing decision. It reuses an unambiguous existing license or established decision; otherwise it asks for a license or explicit deferral. Creation does not begin without an answer. Conflicts are clarified before changes and existing license files are preserved. A deferred decision is reported as unresolved. A selected license is implemented: MIT with a confirmed copyright year and rights holder, other licenses from an explicitly confirmed complete text file. The license file, manifest and documentation are created and checked together. The decision persists in docs/license.md, including explicit deferral.

| Action | Inputs | Result |
| --- | --- | --- |
| marketplace-create | Cloned repository, display name, identifier, publisher | Shared catalog, both host catalogs and standalone tools |
| plugin-create | Separate checkout/path, existing GitHub URL, marketplace, display name, identifier, description, publisher, source skill, languages | Plugin structure without catalogs, association and documentation templates |
| configure | Existing plugin and chosen marketplace | Catalog entry and local mapping; other associations remain |

### Update documentation

Use `update`, or `/plugin-manager:update PATH` in Claude Code. The action rereads current product sources and saved language settings, updates README and guides, then validates them. It installs and publishes nothing. `update-local` is the separate command for refreshing local plugin snapshots.

## Understand the output

New plugins own manifests, skills and documentation, but no marketplace catalogs. The agent completes generated documentation templates from source evidence. `valid` and `structure_valid` describe publishable structure. `local_development.complete` separately describes local development configuration. Missing checkouts or `.local` files are expected on fresh clones and do not invalidate the published catalog. Verification executes no target code.

## Control the session

Existing files are inspected first. Conflicting tooling or mappings stop for targeted review; personal data and installations are preserved. Only plugin-create clones missing checkouts from the supplied existing GitHub source. Configure does not automatically migrate old plugin catalogs.

## Return later

Update reads current sources again. Publish can resume from a private journal after checking actual GitHub state and the original approval. Old release journals require a new plan.

## Specialized workflows

`make install-local TARGET=claude|codex` and `make update-local` use all associated plugins in a shared `<marketplace-id>-dev`. In a plugin, `MARKETPLACE=/path/to/catalog` overrides the local default only for that invocation. Missing required checkouts stop before host changes. `DRY_RUN=1` creates snapshots only.

[Publish](publish.md) treats plugin and marketplace separately: for new entries, plugin first, marketplace second. Branch → commit → push → PR → checks → merge require concrete approval. No tags, releases or plugin ZIPs.

[Technical commands and inputs](../../skills/_shared/references/workflows.md)

Local mappings are written only after Git confirms the proposed ignore rules are effective. Negations exposing `.local/marketplace.json` stop before changes; existing content and associations remain intact. [First publication without HEAD](publish.md#first-publication-without-head) needs separate explicit approval.

Local snapshots read the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `update-local` and open a new host session. Local tests require no commit, push or PR. Keep one shared `<marketplace-id>-dev`, with no additional marketplaces per branch.

`configure` is the normal setup path. `local-marketplace.example.json` is an optional manual copy template. Only `.local/marketplace.json` is read for local runtime mappings; never commit those mappings.

### Skeleton before domain implementation

`plugin-create --skeleton` creates an explicitly unfinished plugin without an existing domain skill source. Reuse known marketplace, technical identifier, display name, existing GitHub repository, publisher and documentation language settings; clarify only missing/conflicting facts. Description is optional; absent a confirmed description, the manifest explicitly says unimplemented. No domain capabilities or license are invented.

```sh
# From ai.plugins; target checkout already exists with Git origin:
make plugin-create ARGS='--root /path/to/plugin --marketplace /path/to/catalog --skeleton --name example-plugin --display-name "Example Plugin" --author "Confirmed publisher" --languages de en --default-language de --license deferred'
```

The existing `--source /path/to/skill` mode remains available; the modes are mutually exclusive. The skeleton contains a visibly marked nonfunctional skill, manifests, association, documentation scaffold, test tools, `SCOPE.md`, `AGENTS.md`, `CLAUDE.md` and `docs/architecture.md`. Differing existing instruction/scope files are not overwritten. Structural validity does not certify domain behavior.

### Compare scope against source

1. Confirm purpose, non-goals and observable acceptance criteria in `SCOPE.md` with the user. Unknown requirements remain draft.
2. Claude/Codex implements within the development rules. Domain runtime belongs under `skills/`, developer tools under `scripts/`; tests follow the shared layout.
3. Explicitly request a scope/source review through `verify`. The skill reads confirmed requirements and actual source/test logic, reporting evidence, deviations, reasons and proposed changes for each requirement.

```sh
make verify SOURCE=/path/to/plugin REVIEW=1
# Without Make, using the trusted Manager helper:
python3 plugins/plugin-manager/skills/_shared/scripts/verify.py --source /path/to/plugin --review
```

These commands collect static evidence; they do not replace the subsequent semantic agent review. `ready_for_source_review` means evidence available, not requirement fulfilled. `needs_attention` reports findings with exit code 1 without changing the meaning of `structure_valid`. All requirements remain semantically `unverified` in the automated report; tests are never executed. The agent then distinguishes `supported_by_source`, `contradicted`, `missing_evidence` and `not_assessed`, citing real file/line evidence. Source support is still not runtime or host acceptance.

SCOPE uses stable headings such as `## R1: Consent before persistence`, with `Status: confirmed`, one `Acceptance:` criterion and individual `Source:` and `Test:` file pointers per requirement. Overall status precedes the requirements. Pointers can reference public source/test files only; private data, fixtures and symlinks are not read as evidence. [Review rules](../../skills/_shared/references/scope-review.md).

Verify never repairs, starts tests or modifies the target scope. Reports appear in conversation by default; saving needs an explicit output path. Agent instructions guide structure but cannot guarantee LLM behavior. Tests and semantic review complement them.
