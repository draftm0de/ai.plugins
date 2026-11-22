# Usage

New skeleton pages are filled with the actual scaffold status in the selected languages and validated before writes. Existing prose is preserved. Final checks separately assess the actual plugin structure, marketplace and documentation. Errors in preserved pages remain visible; `checks.status=needs_attention` means creation still has outstanding findings. `passed` also checks technical consistency of licensing files and documentation; it does not establish legal suitability or functional acceptance. The completion report also states the licensing decision, actual license files and tests or host checks still pending.

[Deutsch](../de/usage.md) | **English**

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.en.md) · [Guides](README.md)

## Set up

Targets come from your open project or explicit input, never automatically from the Manager installation. Existing project facts and Git origin are reused; only missing or conflicting inputs need clarification. Display name and technical identifier are distinct. Publisher, license and skill behavior are never invented.

## Choose a workflow

In Claude Code use `/plugin-manager:plugin-manager` (marketplace setup and plugin creation) or `/plugin-manager:configure`. In Codex/GPT select the capability or describe the action. `init` is unsupported.

The central `plugin-manager` entry first reads the project state and uses the saved operator language, asking explicitly if none is stored. It asks whether the workpackage is configured as a plugin or a marketplace, runs the guided configuration while no configuration evidence exists and then synchronizes the skeleton. Documentation languages remain independent. Questions are asked in small coherent steps; unanswered configuration facts prevent generator writes. Existing plugins are not recreated: after any needed skeleton work the entry reports the state and waits. Use the separate `configure` skill explicitly to associate an existing plugin with a marketplace.

Before creation, the agent resolves the licensing decision. It reuses an unambiguous existing license or established decision; otherwise it asks for a license or explicit deferral. Creation does not begin without an answer. Conflicts are clarified before changes and existing license files are preserved. A deferred decision is reported as unresolved. A selected license is implemented: MIT with a confirmed copyright year and rights holder, other licenses from an explicitly confirmed complete text file. The license file, manifest and documentation are created and checked together. The decision persists in docs/license.md, including explicit deferral.

| Action | Inputs | Result |
| --- | --- | --- |
| plugin-manager (kind marketplace) | Cloned repository, display name, identifier, publisher | Shared catalog, both host catalogs and standalone tools |
| plugin-manager (kind plugin) | Separate checkout/path, existing GitHub URL, marketplace, display name, identifier, description, publisher, skeleton mode, languages | Plugin structure without catalogs, association and documentation templates |
| configure | Existing plugin and chosen marketplace | Catalog entry and local mapping; other associations remain |

### Update documentation

Use `update`, or `/plugin-manager:update PATH` in Claude Code. The action rereads current product sources and saved language settings, updates README and guides, then validates them. It installs and publishes nothing. `install-local` is the separate command for refreshing local plugin snapshots.

## Understand the output

New plugins own manifests, skills and documentation, but no marketplace catalogs. The agent completes generated documentation templates from source evidence. `valid` and `structure_valid` describe publishable structure. `local_development.complete` separately describes local development configuration. Missing checkouts or `.local` files are expected on fresh clones and do not invalidate the published catalog. Verification executes no target code.

## Control the session

Existing files are inspected first. Conflicting tooling or mappings stop for targeted review; personal data and installations are preserved. Only plugin-create clones missing checkouts from the supplied existing GitHub source. Configure does not automatically migrate old plugin catalogs.

## Return later

Update reads current sources again. Publish can resume from a private journal after checking actual GitHub state and the original approval. Old release journals require a new plan.

## Specialized workflows

`make install-local TARGET=claude|codex` use all associated plugins in a shared `<marketplace-id>-dev`. In a plugin, `MARKETPLACE=/path/to/catalog` overrides the local default only for that invocation. Missing required checkouts stop before host changes. `DRY_RUN=1` creates snapshots only.

[Publish](publish.md) treats plugin and marketplace separately: for new entries, plugin first, marketplace second. Branch → commit → push → PR → checks → merge require concrete approval. No tags, releases or plugin ZIPs.

[Technical commands and inputs](../../skills/_shared/references/workflows.md)

Local mappings are written only after Git confirms the proposed ignore rules are effective. Negations exposing `.local/marketplace.json` stop before changes; existing content and associations remain intact. [First publication without HEAD](publish.md#first-publication-without-head) needs separate explicit approval.

Local snapshots read the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. Local tests require no commit, push or PR. Keep one shared `<marketplace-id>-dev`, with no additional marketplaces per branch.

`configure` is the normal setup path. `local-marketplace.example.json` is an optional manual copy template. Only `.local/marketplace.json` is read for local runtime mappings; never commit those mappings.

### Skeleton before domain implementation

`plugin-create --skeleton` creates an explicitly unfinished plugin without an existing domain skill source. Reuse known marketplace, technical identifier, display name, existing GitHub repository, publisher and documentation language settings; clarify only missing/conflicting facts. Description is optional; absent a confirmed description, the manifest explicitly says unimplemented. No domain capabilities or license are invented.

```sh
# From ai.plugins; target checkout already exists with Git origin:
python3 -B skills/_shared/scripts/workflows.py plugin-create --root /path/to/plugin --marketplace /path/to/catalog --skeleton --name example-plugin --display-name "Example Plugin" --author "Confirmed publisher" --languages de en --default-language de --license deferred
```

Creation supports only `--skeleton`; `--source` and `--import` are rejected before writes. The skeleton contains a visibly marked nonfunctional skill, manifests, association, documentation scaffold, test tools, `SCOPE.md`, `AGENTS.md`, `CLAUDE.md` and `docs/architecture.md`. Differing existing instruction/scope files are not overwritten. Structural validity does not certify domain behavior.

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

### Project setup (central entry)

Skill `plugin-manager` (command file `commands/plugin-manager.md`; Claude Code normally namespaces it as `/plugin-manager:plugin-manager`, not host-tested) prepares an explicitly selected folder (a workpackage): it checks the operator language, asks whether the workpackage is configured as a plugin or a marketplace, adds the skeleton of that kind and records ownership. The embedded Manager itself is not a target. Configuration evidence and skeleton evidence are kept per running plugin under `.project/plugins/<plugin>/` (`config.json`, `skeleton.json`).

```sh
python3 -B skills/_shared/scripts/project_setup.py status --target <folder> --plugin plugin-manager
python3 -B skills/_shared/scripts/project_setup.py setup  --target <folder> --plugin plugin-manager [--language <tag>]
python3 -B skills/_shared/scripts/project_setup.py record --target <folder> --plugin plugin-manager --kind plugin|marketplace --artifact <name>
```

Handled files: the synced files of the configured kind, listed with hash and executable bit in the generated `skills/_shared/manifests/<kind>.sync.json` (for a plugin this includes the helper `project_setup.py`, `operator_language.py` and the flows `entry`, `language`, `skeleton`, `sync`), copied byte for byte from `skills/_shared/templates/<kind>/sync/` (parent folders are created); the helper refuses to copy a source whose bytes differ from the recorded hash. Files in `skills/_shared/templates/<kind>/seed/` are only created once by the generators and never synced. `status` writes nothing. The skill asks for a missing language and then runs `setup`; a concrete read-only request only runs `status`.

`setup` never changes the bytes of an existing file (besides the management files: `.gitignore` gets the exact rule line, `.project/operator.json` stores the language, `.project/plugins/plugin-manager/skeleton.json` gets hash pairs). A managed file that differs from the template is a *content deviation* (listed under `different`). It is only replaced by an explicit `adopt` decision of the `sync` operation (see below); files are removed only under the removal rules below. A *technical conflict* (invalid or unsupported configuration or skeleton evidence, the former `.project/plugin.skeleton.lock.json`, corrupt language file, symlink or traversal, file where a folder is needed, unreadable file, missing template source, non-target) stops before any write. Before saving the first language `/.project/operator.json` is added to `.gitignore` (only that exact line; other rules and negations are not evaluated). `.project/plugins/plugin-manager/skeleton.json` is meant to be committed: `{"schema_version": 2, "files": {"<path>": {"source_hash": "<sha256>", "local_hash": "<sha256>"}}}`. Only this format is supported: an older (v1) or invalid lock is rejected before any write, left unchanged and never migrated. A missing lock is allowed, but deviating files are then not accepted. Other valid entries are kept.

JSON result: `ok`, `conflicts`, `errors`, `files` (path to missing/identical/accepted/decision_needed), `missing`, `identical`, `different`, `created` (including `unverified` for copied files whose check failed), `language` (`needs_choice`, `saved`), `gitignore`, `lock` (`changed`, `pending`), `configuration` (`plugin`, `configured`, `kind`), `matches_template`. Exit codes: 0 success (deviations or a missing language are not errors), 1 technical conflict or write failure (partial changes under `created`), 2 invalid invocation. No Git, installation, network or target code is used; the helper and the flows `entry`, `language`, `skeleton`, `sync` ship byte-identically in every generated plugin, together with custom stubs (`skills/<name>/SKILL.md`, `skills/<name>/flows/configure.md`, `skills/_shared/manifests/default.json`).

Technical errors that appear during writing (symlink or folder where a file was verified, read failure, filesystem error) are reported under `conflicts`/`errors` with exit 1, never as deviations; writing stops, no further ownership evidence is recorded and the actual partial changes stay listed. `status` also lists the management folder `.project` under `missing.directories` while it is needed.

#### State-driven entry

`/plugin-manager:plugin-manager` (host activation by this name is untested) loops: `status` → run exactly the needed flow → `status` again. `status` writes nothing and needs no `plugin.json`, Git, origin or marketplace. Answer fields: `state` (`plugin`, `marketplace`, `unconfigured`, `conflict`), `plugin_configured`, `configuration`, `next`, `language` (`operator_language`, `needs_choice`), `skeleton` (`open`, `missing_files`, `lock_pending`, `ignore_rule_pending`, `different`), `files`, `conflicts` (each with optional `code`, `entries`). `next` has a fixed priority: `stop` (technical conflict) → `language` → `configure` (no configuration evidence `.project/plugins/<plugin>/config.json`) → `skeleton` → `sync` (a managed file needs a keep/adopt decision) → `ready`. `ready` only means the workpackage is configured and no automatic flow is open; the entry then prints only the line `Plugin plugin-manager Status: fully configured` (German: `vollständig konfiguriert`) and waits. Accepted deviations stay listed under `skeleton.different` and are never overwritten or re-routed.

Flows: `language --target <folder> --language <tag>` (ignore rule first, then `operator_language.py`); configuration in the same folder (asks "plugin or marketplace?" first, runs the existing plugin-create generator and only after a passed run `record`, which writes `config.json`); `setup --target <folder>` (the skeleton: the synced files of the configured kind, parent folders, ignore rule, skeleton evidence; it invents no `plugin.json`). `setup` and `sync` refuse an unconfigured target with `not_configured`. Both helper flows answer `next: "status"` on success and `next: "stop"` on failure. A folder without configuration evidence is accepted when it holds only `.git/`, `.idea/` (checked as directories, never opened), a regular UTF-8 `.gitignore` and valid `.project` metadata, or when it already holds a root `plugin.json` or `marketplace.json` (a product, never evidence); other content (`code: not_fresh`), an invalid product file or the embedded Manager stop before writes. GitHub origin and marketplace are prerequisites of the configuration flow only; if they are missing, the entry names them and waits without rolling back anything already created. Exit codes as above.

#### Sync of existing managed files

For each managed file the skeleton evidence (`skeleton.json`) stores the pair `{source_hash, local_hash}` last accepted. Rules: missing locally → copied, both hashes recorded after verification; local equals the template → missing or stale pair corrected without a dialogue; local differs and the current pair equals the stored pair → *accepted*, no dialogue, no writes (and never `matches_template`); template or local changed since the accepted pair, or no pair, while the contents differ → *decision needed*. `status` lists these under `sync.decisions` (`path`, `reason`, `source_hash`, `local_hash`, `accepted`, `source_changed`, `local_changed`, `source_file`, `local_file`) and `next: "sync"`; it writes and asks nothing. The skill shows only the file path and the fact that differences exist, without file contents, excerpts, diffs or content summaries and explicitly asks "keep local file" or "adopt template".

`sync --target <folder> --decision keep|adopt --path <path> --source-hash <h> --local-hash <h>` applies one decision for exactly the shown pair: `keep` keeps the local bytes and records both current hashes; `adopt` replaces only this file with the template (mode kept), verifies it and records `{template, template}`. If the pair changed meanwhile it stops with `stale_decision` and writes nothing. Cancellation, silence or a preselection is no decision and persists nothing. Exit 0 and `ok: true` (answer `changed.file`, `changed.lock`, `next: "status"`) is success; exit 1 reports conflicts or partial changes. Files are removed only as described under *Removal*, folders are not hashed or moved, extra local files are kept and `AGENTS.md` is not managed. The plugin-create generator neither judges nor replaces an existing managed skeleton file (also a deviating or kept one); differences are resolved only through sync once the configuration evidence exists.

#### Removal (source removed in the parent template)

A removed source is recognized only through its tombstone, the path in `removed` of the generated `<kind>.sync.json`. A tombstoned path means "removed"; a missing, invalid or hash-mismatching source, a missing template base, symlinks, wrong types and read errors are technical conflicts and never a removal. `status` reports `removals` separately: `auto` (owned and untouched: current local hash equals the stored `local_hash` and the stored `source_hash`), `decisions` (changed or deliberately accepted local file: always asked), `kept` (kept earlier and unchanged), `unowned` (no lock evidence: never touched) and `lock_cleanup` (owned file already gone). The skeleton flow (`setup`) executes `auto` and `lock_cleanup`: it deletes only the verified files, drops their lock entries and removes now-empty parent folders of the removed files bottom-up with `rmdir`; never needed skeleton folders, the project root, `.git`, `.idea` or `.project`, and never foreign files. The question is answered with `sync --decision keep|delete --path <path> --source-hash removed --local-hash <h>`; no file content, excerpt or diff is shown. `keep` stores `{"source_hash": null, "local_hash": "<sha256>"}` (a documented extension of lock schema 2, set only by this decision): an unchanged repetition does not ask again, a later local change does, and a returning source is classified normally. `setup` and `sync` report `removed.files` and `removed.directories` (actual partial changes on errors).
