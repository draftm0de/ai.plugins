# Current-format policy / Aktuelle Formate

Status: confirmed

This scope records the approved compatibility boundary and creation interaction requirements, not a complete product acceptance. Every requirement states only the current target; history lives in Git. Requirement ids are stable and never reused; R19 was withdrawn.

## R1: No backwards compatibility

Status: confirmed
Acceptance: Only current documented formats and entry points are supported. Reject obsolete formats without automatic inference, migration or modifying user data.
Source: skills/_shared/WORKFLOWS.md
Source: scripts/plugin.py
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/scripts/documentation.py
Test: tests/integration/update/test_documentation.py
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/integration/test_shared_installer.py

## R2: Resolve the licensing decision before plugin creation

Status: confirmed
Acceptance: Before creation writes, the agent reuses an unambiguous existing target license or explicit session decision; otherwise it asks for a license or explicit deferral and waits for the answer. Conflicts require clarification and existing license content is preserved. Silence is not deferral. The completion report identifies a deferred decision as unresolved and distinguishes a selected license from files actually created.
Source: skills/setup/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R3: Separate conversation language from documentation language

Status: confirmed
Acceptance: Creation through the setup skill uses the project-scoped operator-language gate of R12/R14. Documentation languages are resolved independently and never determine the operator language implicitly. The former standalone plugin creation entry is removed.
Source: skills/setup/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R4: Complete skeleton documentation and report creation checks

Status: confirmed
Acceptance: New skeleton documentation contains localized, evidence-based scaffold content without unresolved placeholders for every selected language. No domain capabilities or test success are invented. Existing user prose is preserved and its validation failures remain visible. Creation checks actual plugin and marketplace structure and documentation, reports their results separately from licensing, pending functional acceptance and unexecuted tests/host checks, and does not claim completion on failed checks.
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/flows/configure.md
Test: tests/integration/plugin_create/test_workflows.py

## R5: Guided plugin creation dialogue

Status: confirmed
Acceptance: Missing setup inputs are collected using the host's available structured question tool in small coherent groups. Unknown conversation language is asked alone first and the agent waits before continuing in that language. Confirmed inputs are not asked again. When no structured tool is available, the agent explains this limitation and asks one concise question at a time in chat instead of dumping a questionnaire. No target writes occur while required answers are missing.
Source: skills/setup/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R6: Implement confirmed licensing and persist the decision

Status: confirmed
Acceptance: `create --kind plugin` requires an explicit license identifier or explicit deferral before writes. A selected MIT license creates the standard license with confirmed copyright year and holder; another selected license uses an explicitly confirmed complete file without alteration. Missing inputs, unsupported templates and conflicting existing license files fail before plugin/marketplace writes. Existing matching license bytes are preserved. Selected licensing appears in plugin and derived host manifests, and new documentation in every selected language links to the persisted decision and license file. Explicit deferral is persisted without claiming a license. Final checks distinguish implemented, deferred and inconsistent licensing; existing prose is preserved and missing licensing documentation is reported.
Source: skills/_shared/scripts/licensing.py
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/flows/configure.md
Test: tests/integration/plugin_create/test_licensing.py

## R7: Repeated creation detects existing products before license validation

Status: confirmed
Acceptance: An existing target product is rejected before licensing validation or creation writes, even with missing/conflicting licensing arguments. Unknown conversation language is resolved alone before offering existing-plugin actions; known language is used exclusively. The setup skill does not recreate an existing plugin; after language/skeleton handling it reports ready and waits under R12/R14. The former standalone existing-plugin action dialog is removed. Existing files and marketplace entries remain unchanged.
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R8: Skeleton-only plugin creation

Status: confirmed
Acceptance: `create --kind plugin` creates only a new nonfunctional skeleton. Its dialogue offers no skill import or mode choice and requests no source skill path. The public helper rejects --source and --import before writes, including when combined with --skeleton. Other actions retain their own source-reading options. Existing source directories and target/marketplace data remain unchanged on rejected import calls.
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R9: Project-scoped operator language for generated plugins

Status: confirmed
Acceptance: Every newly generated plugin ships the shared operator-language helper and its reference. Before setup/domain interaction, a missing project preference is asked alone and persisted only after an explicit answer. Later calls reuse it, including bare slash commands and new sessions. An explicit change updates only that project's preference. Content/documentation languages remain independent; invalid state is rejected without mutation. Future skills preserve the same gate.
Source: skills/_shared/templates/plugin/sync/skills/_shared/scripts/operator_language.py
Source: skills/_shared/templates/plugin/sync/skills/_shared/references/operator-language.md
Source: skills/_shared/scripts/workflows.py
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/operator_language_acceptance.md

## R10: Manager copy and delivery of the operator-language building block

Status: confirmed
Acceptance: The generator template remains the canonical source of the operator-language helper and reference; the Manager ships byte-identical standalone copies under skills/_shared/ as a delivery requirement. Their only Manager use is the setup skill, which is separately authorized by R11; no other workflow uses them. The plugin generator template ignores exactly /.project/operator.json (no blanket .project/ rule, no duplicates); only newly created plugin repositories receive it, while marketplace repositories and existing plugins configured later keep their .gitignore. `create --kind plugin` ships helper and reference, never runs the helper and stores no preference. The helper does not edit .gitignore. Entry-point use (only R11's setup entry), skeleton sync and adoption by other plugins are not part of this requirement.
Source: skills/_shared/scripts/operator_language.py
Source: skills/_shared/references/operator-language.md
Source: skills/_shared/scripts/workflows.py
Test: tests/unit/operator_language/test_validation.py
Test: tests/integration/operator_language/test_cli.py
Test: tests/integration/plugin_create/test_operator_language_delivery.py

## R11: The setup skill sets up operator language and missing shared development files

Status: confirmed
Acceptance: The setup skill (/plugin-manager:setup), for an explicitly selected folder (never the installed Manager directory or the embedded Manager), checks operator language and the closed list of managed files of the configured kind (R16) without writes, stops on technical conflicts before any write, asks for a missing language, then adds only missing files/folders from the generator template, ensures the exact ignore rule /.project/operator.json before the first language write, stores the language through operator_language.py and records, per verified path, the pair {source_hash, local_hash} of full SHA-256 hashes in .project/plugins/plugin-manager/skeleton.json (schema_version 2, the only supported format: an older, unknown or invalid file is rejected before writes and left unchanged, never migrated; the former .project/plugin.skeleton.lock.json is an unsupported location). The skeleton setup copies missing files and corrects missing or stale pairs of template-identical files; it never changes the bytes of an existing file. Existing files that differ are only changed by the explicit sync decision of R12; the only other files setup may modify are .gitignore (adding the exact rule) and .project/operator.json, each as specified. Technical errors (symlink, wrong type, unreadable, filesystem errors) are reported as such, never as content deviations, and stop further writes while actual partial changes stay listed. Concrete read-only requests only run the status. No Git, installation, network or target code. Other plugins and host activation by slash command are not part of this requirement; updating and removing existing files is governed only by R12.
Source: skills/setup/scripts/setup_state.py
Source: skills/setup/SKILL.md
Test: tests/integration/project_setup/test_setup.py
Test: tests/contracts/test_plugin_manager_entry.py

## R12: The setup skill dispatches by state: language, configuration, skeleton, sync

Status: confirmed
Acceptance: /plugin-manager:setup reads a write-free status of an explicitly selected folder and runs exactly the needed flow, re-checking after every successfully completed flow. Priority as in R17: technical conflict (stop), operator language missing (language flow), configuration evidence missing (configuration flow), skeleton additions or skeleton evidence missing (skeleton flow), a managed file needing a keep/adopt decision (sync flow), otherwise ready. The skeleton is the sync list of the configured kind (R16) with parent folders, the ignore rule and skeleton evidence; it needs no plugin.json, Git, origin or marketplace and invents no identity. A folder without plugin.json is accepted when it holds only .git/.idea (checked as directories, never opened), a regular UTF-8 .gitignore, valid .project metadata and skeleton paths, including the entry's own earlier output; other content, an invalid plugin.json or the embedded Manager stop before writes. Sync rules per managed file: missing locally, copy from a valid source and record both hashes after verification; source and local identical, correct a missing or stale pair without a dialogue; source and local differ and the stored pair equals the current pair (source_hash and local_hash both), the deviation is accepted without dialogue or writes; source or local changed since the accepted pair (or no pair, or no lock) while contents differ, a decision is required and nothing is overwritten automatically. Status reports path, hashes, reason and decision need structurally and asks nothing; the skill shows only the file path and the fact that differences exist, without file contents, text excerpts, diffs or content summaries, and explicitly asks for "keep local file" or "adopt template" in the operator language. Keep leaves the local bytes and records both current hashes; adopt replaces only the explicitly selected file (mode kept), verifies it and records both hashes. Cancellation, silence or a preselection is no decision and persists nothing; a decision holds only for the shown pair and a changed pair stops for a new check. Removal rules for a managed path whose source was removed in the parent template (a single missing source of a listed path, while the template base exists and holds at least one managed source; a missing or invalid base, symlinks, wrong types and read errors are technical conflicts, never removal): the file is deleted automatically only if the lock proves ownership and the current local hash equals the stored local_hash and the stored source_hash; a changed or accepted local file always requires an explicit "keep local file" or "delete local file" question (no content, excerpt, diff or summary is shown, only the path and that the source was removed); without lock evidence nothing is deleted; a locally missing owned file only loses its lock entry; keep records source_hash null with the current local_hash (a documented extension of lock schema_version 2, set only by this decision), so an unchanged repetition does not ask again and a later local change does; a returning source is classified normally again. After removal only empty parent folders of the removed file go, bottom-up with rmdir, never needed skeleton folders, the project root, .git, .idea or .project, and foreign files are never deleted. Status reports automatic removals, questions, kept files, unowned files and lock cleanup separately, writes nothing, and the skeleton flow executes the automatic part. Folders are not hashed or moved, extra local files are kept, AGENTS.md is not managed and new managed files need an entry in the fixed list; a removed source stays recognizable only while its path remains in that list. For the explicitly requested manual sync test, keep.md and remove.md are in that list. Accepted deviations cause no sync routing and never mean matches_template; ready is not product acceptance. Configuration runs after language and before the skeleton (R17) in the same call and folder through the existing `create --kind plugin` generator and its rules, with inputs, GitHub origin and marketplace asked or reported as external prerequisites, never invented, rolled back or changed without explicit selection; a generator collision with a deviating or deliberately kept skeleton file changes nothing and stops openly, to be resolved only by the sync flow. Read-only requests run one status only. Errors and missing progress stop with concrete reasons and actual partial changes; ready waits for input. Dialogue and flow text is instruction evidence, not model or host behavior; concurrent writers are organizationally excluded.
Source: skills/setup/scripts/setup_state.py
Source: skills/setup/SKILL.md
Source: skills/setup/flows/language.md
Source: skills/setup/flows/skeleton.md
Source: skills/setup/flows/configure.md
Source: skills/setup/flows/sync.md
Test: tests/integration/project_setup/test_fresh.py
Test: tests/integration/project_setup/test_sync.py
Test: tests/integration/project_setup/test_removal.py
Test: tests/contracts/test_plugin_manager_entry.py

## R13: Managed Claude compatibility file

Status: confirmed
Acceptance: The plugin generator and the skeleton flow of the setup skill share a CLAUDE.md template containing only an English compatibility comment and @AGENTS.md. All agent instructions belong in AGENTS.md. Missing CLAUDE.md is copied and its hash pair recorded in the skeleton lock, identical content is preserved and recorded, and existing different content is preserved until an explicit sync decision (R12) keeps or replaces it; it is never overwritten automatically. A fresh folder containing this skeleton file remains initializable. AGENTS.md is not added to skeleton management.
Source: skills/_shared/templates/plugin/sync/CLAUDE.md
Source: skills/setup/scripts/setup_state.py
Test: tests/integration/project_setup/test_setup.py
The same compatibility CLAUDE.md applies to every kind (plugin, marketplace) and to this repository itself; a differing "Project instructions" variant is not used.

## R14: Creation through the setup skill

Status: confirmed
Acceptance: Plugin creation has no separate public plugin creation skill or command wrapper. The configuration flow of the setup skill owns the guided creation instructions and uses the existing internal `create --kind plugin --skeleton` generator. Licensing, preservation and creation checks remain required. Existing marketplace associations are handled by the associate flow of R21 (the former configure skill is removed). Creation uses the saved operator-language gate of R12; former standalone entry dialogue rules do not create another public entry.
Source: skills/setup/flows/configure.md
Test: tests/contracts/test_skill_entrypoints.py
Test: tests/contracts/test_plugin_manager_entry.py

## R15: Workpackage configuration evidence per running plugin

Status: confirmed
Acceptance: The setup skill keeps the configuration evidence in the workpackage under .project/plugins/plugin-manager/config.json (the helper receives the plugin name as --plugin plugin-manager). Format: {schema_version: 2, plugin, kind, artifact, configured_at, marketplace}; kind is plugin or marketplace (the kinds of the manifests); artifact is the name of the created plugin or marketplace; configured_at is an ISO-8601 UTC timestamp; marketplace is {name} (the name is the identity of a marketplace; it has no repository of its own) for a kind whose manifest says requires_marketplace (plugin) and null for every other kind. The file is committed; schema_version 1 and a missing, partial or unexpected marketplace property are an unsupported format (conflict before any write, unchanged, no migration). A plugin belongs to exactly one marketplace, so its configuration is complete only with that identity (R21); ready therefore includes the association, without a further gate. The machine-specific path of that marketplace is never part of this file: it lives in the Git-ignored .project/plugins/<plugin>/local.json ({schema_version: 1, marketplace_path}, strictly validated). The file is written only after a successful configuration run (generator checks passed) and never earlier. A workpackage is configured for a plugin only if this file is valid; a root plugin.json or marketplace.json is a product, never evidence. Evidence of other plugins (other folders under .project/plugins/) does not configure this one. Missing, unreadable, extra-key, wrong-type, unknown-kind or plugin-mismatching files are reported as conflicts before any write, leave all data unchanged and are never migrated. Status reports configuration {plugin, configured, kind}. The helper operation record writes the file only after a passed configuration run and, for a kind with requires_marketplace, only if local.json names a marketplace checkout whose marketplace.json lists the plugin (name and the plugin's repository URL); it takes the identity {name} from that checkout and otherwise refuses with association_missing ("associate first") without writing.
Source: skills/setup/scripts/setup_state.py
Source: skills/setup/SKILL.md
Test: tests/integration/project_setup/test_workpackage_config.py

## R16: Skeleton per kind: sync/ and seed/ folders, generated hash file, manifest

Status: confirmed
Acceptance: Every kind has two template folders: skills/_shared/templates/<kind>/sync/<project path> (files kept in sync: copied 1:1, hashed in .project/plugins/<plugin>/skeleton.json, schema_version 2, and synchronized under the keep/adopt/delete rules of R12) and skills/_shared/templates/<kind>/seed/<project path> (files created once when missing, with a short intro of what the file is for, never what it does; never hashed or synced). The folder a file lies in is the only statement of its class. skills/_shared/manifests/<kind>.json is only {schema_version: 1, product, requires_marketplace, derived: [{path, generate, check}]} (product = root file naming the kind or null; requires_marketplace = boolean, true only for the kind plugin; derived = catalogs produced by a named command of the kind and only verified by its check command, never copied or hashed). skills/_shared/manifests/<kind>.sync.json is generated, never edited by hand: {schema_version: 1, files: {<path>: {sha256, executable}}, removed: [<path>]}, sorted, with a trailing newline. files lists exactly the files of sync/ (full SHA-256 of the bytes, executable bit); removed lists tombstones, paths whose template source was removed in the parent (plugin: keep.md, remove.md), and may not overlap files. The development tool scripts/skeleton_hashes.py (make build-skeleton-hashes / check-skeleton-hashes) writes the file (build keeps removed) and verifies it (check exits 1 naming each path on a hash or executable mismatch, a missing or unlisted file, an invalid file or an overlap); check runs in both CI workflows of this repository, never in generated repositories. The helper trusts the file only as the expected value: before copying or comparing it hashes every source of sync/ and refuses with a template_base conflict (reason names make build-skeleton-hashes) on a deviating or missing source of a listed path, an unlisted file in sync/, an invalid sync file or an overlap, and writes nothing. The removal rules of R12 apply only to paths in removed. Templates and manifests carry -text in .gitattributes so line endings never change a hash. The kind marketplace has sync = CLAUDE.md and scripts/{local_plugins,marketplace,plugin_payload,run_tests,verify}.py; seed = Makefile (only install-local and test), AGENTS.md, SCOPE.md, docs/architecture.md, docs/prerequisites.md, local-marketplace.example.json, tests/README.md, tests/__init__.py, tests/contracts/__init__.py, tests/contracts/test_structure.py; derived = .claude-plugin/marketplace.json and .agents/plugins/marketplace.json (marketplace.py sync / check). The kind plugin has AGENTS.md, CLAUDE.md, the standards under docs/standards/, scripts/plugin.py, scripts/run_tests.py, scripts/verify.py and the operator-language building block of R9/R10 in sync/; the setup flows and project_setup.py are no part of a generated plugin. Its seed/ holds the generator files (CUSTOM.AGENTS.md, SCOPE.md, Makefile, ci.yml, gitignore.txt, assets/icon.png as a neutral placeholder, docs, tests). The former .project/plugin.skeleton.lock.json is an unsupported location (no read, migration or deletion). The ignore rules written by the generators are /.project/operator.json (new plugin repositories only) and /.project/plugins/*/local.json (every plugin repository where the association is written; effectiveness is checked with Git before writing); the marketplace side keeps .local/. A managed file that was an exact copy of the source at the last sync and is untouched since (its source changed, the local file did not) is updated by `setup` without a question, named by path; a file that was edited or deliberately kept (keep) is never replaced silently and comes as a decision under R12.
Source: skills/setup/scripts/setup_state.py
Source: scripts/skeleton_hashes.py
Source: skills/setup/scripts/state/context.py
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/integration/project_setup/test_manifest.py
Test: tests/integration/project_setup/test_sync_files.py
Test: tests/unit/skeleton_hashes/test_skeleton_hashes.py
## R17: Dispatch order and kind selection

Status: confirmed
Acceptance: The status priority is: technical conflict (stop), operator language missing (language), workpackage not configured for the running plugin (configure), skeleton additions or evidence missing (skeleton), managed file needing a decision (sync), otherwise ready. The configure flow first asks "plugin or marketplace?" (explicit answer, no preselection); plugin starts the plugin setup flow, marketplace the marketplace flow (R20); an existing root plugin.json is named and stops the plugin branch. A marketplace.json in the root is no conflict once the kind is marketplace. The generator creates only product files and never touches, judges or fails on existing managed skeleton files; skeleton differences are resolved by the skeleton and sync flows after the configuration evidence exists. Flow success is re-checked by status; after configuration both the evidence of R15 and the skeleton files of the chosen kind exist.
Source: skills/setup/scripts/setup_state.py
Source: skills/setup/SKILL.md
Source: skills/setup/flows/configure.md
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/contracts/test_plugin_manager_entry.py

## R18: Ready output

Status: confirmed
Acceptance: When status is ready, the setup skill outputs only the line "Plugin <name> Status: fully configured" (`<name>` is the configured plugin or marketplace repository from the status answer, not the running Manager) in the operator language (German: "Plugin <name> Status: vollständig konfiguriert") and waits. Skeleton deviations and other details are not listed unless asked.
Source: skills/setup/SKILL.md
Test: tests/contracts/test_plugin_manager_entry.py

## R20: Marketplace setup is part of the setup skill

Status: confirmed
Acceptance: The marketplace setup is a flow of the setup skill; there is no skill skills/marketplace-create and no commands/marketplace-create.md. The complete procedure is skills/setup/flows/marketplace.md (no reference to a separate skill). flows/configure.md asks "Plugin or marketplace?" first (R17), holds the dialogue rules shared by both kinds (section "Guided dialogue (both kinds)") and hands over to flows/marketplace.md for the marketplace. The cloned marketplace folder is the working folder. Technical name (kebab-case), display name and owner/publisher are asked one at a time or in small coherent groups, never invented and never taken from the Git author; an existing marketplace.json supplies missing values ; the marketplace needs a Git repository but no origin and records no repository of its own. Nothing is written before the facts are answered. The helper call is workflows.py create --kind marketplace --root <folder> --name ... --display-name ... --owner ...; success is exit 0 (the answer carries action, changed and published: false, but no ok or checks), then record --kind marketplace --artifact <name> writes the configuration evidence, then status leads to the skeleton flow (hash evidence) and ready. Repeating the operation is idempotent; an identity conflict stops without writes; a plugin repository (plugin.json) is no marketplace. As in R17 the generator neither judges nor replaces an existing synced file listed in manifests/marketplace.sync.json (a deviating one stays byte-identical and surfaces as a sync decision afterwards); seed files never change existing files. The generated starter READMEs name only existing commands (python3 -B scripts/verify.py, python3 -B scripts/marketplace.py sync|check, make install-local), never removed make targets.
Source: skills/setup/flows/marketplace.md
Source: skills/setup/flows/configure.md
Source: skills/_shared/scripts/workflows.py
Test: tests/contracts/test_plugin_manager_entry.py
Test: tests/contracts/test_skill_entrypoints.py
Test: tests/integration/marketplace_create/test_workflows.py

## R21: Marketplace association is a flow of the setup skill; a plugin belongs to exactly one marketplace

Status: confirmed
Acceptance: A plugin belongs to exactly one marketplace; that is a mandatory property of its configuration (R15): the committed config.json carries the identity {name}, the Git-ignored .project/plugins/plugin-manager/local.json ({schema_version: 1, marketplace_path}, strict) the path of the checkout on this machine. The former plugin-side .local/marketplace.json (default marketplace and named associations) is neither written nor read, there is no fallback and no migration; the marketplace side keeps the checkouts of its plugins under sources in its own .local/marketplace.json. The association is the flow skills/setup/flows/associate.md; there is no skill skills/configure and no commands/configure.md, and the helper operation configure is replaced by workflows.py associate --root <plugin> --marketplace <local path of the target marketplace> [--plugin plugin-manager] [--drop-missing-old]. associate requires the configuration evidence (schema 2) of a kind with requires_marketplace and a plugin.json whose name equals the artifact; it validates the target structurally as a marketplace (marketplace.json with a name at its root, no plugin.json, valid catalogs; no configuration evidence of the target is required), plugin and marketplace are separate repositories, the plugin identity must not belong to another repository, neither .local of the marketplace nor local.json of the plugin may be tracked and the ignore rules must be effective. The same marketplace (same name) is idempotent: a fresh clone or moved checkout only gets its local.json. The same checkout under a new name (the path the plugin already records in local.json leads to this checkout, which lists the plugin; the marketplace was renamed, R24) is an identity update of the same marketplace: only the identity in config.json changes, no catalog entry, and no other marketplace is involved. Changing to another marketplace writes in ONE rollback-capable transaction: entry and sources of the plugin in the new marketplace, removal of exactly this plugin's entry (matching name and the plugin's repository URL) and of its sources mapping from the old marketplace, both host catalogs of both marketplaces regenerated, the identity in config.json and the path in local.json. The old marketplace is found through local.json and must carry the name of the identity; if it is not available locally the change is refused unless --drop-missing-old is given, which releases only the local reference and the identity and reports old_catalog_entry_remains: true because the committed catalog line of the old marketplace has to be removed there. The first association happens through plugin creation, which validates the marketplace exactly like associate (a name at its root) before any file is written and then writes local.json and refuses an existing association to another marketplace ("use associate to change"). associate creates no development tools, never commits, pushes, installs or publishes; its answer has action, changed, from, to, published: false, old_catalog_entry_remains and a note that the changed files (config.json of the plugin, marketplace.json and host catalogs of the marketplaces involved) are committed files left unversioned and are published through publish. project_setup status reports for a kind with requires_marketplace the read-only field association {marketplace, path, state: ok|path_missing|path_invalid|mismatch|unsupported}; it never gates ready, never writes and treats a missing local.json (fresh clone) as a hint only. The setup skill routes a request to set, change or move the marketplace of a plugin, after the language gate, to the flow, which asks the local path of the target marketplace as an explicit choice (a suggestion is not a selection). The runtime of the plugin (install-local) and the read-only verification read the path only from local.json; their messages name the plugin-manager association instead of "configure". `install-local` knows no marketplace override (no `--marketplace` option, no `MARKETPLACE` make variable, no `marketplace_root` parameter); the marketplace comes only from `.project/plugins/plugin-manager/local.json`, and the existing check that the plugin is linked in that marketplace stays.
Source: skills/setup/flows/associate.md
Source: skills/setup/SKILL.md
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/scripts/setup_state.py
Test: tests/integration/associate/test_associate.py
Test: tests/integration/associate/test_workflows.py
Test: tests/integration/modify/test_modify.py
Test: tests/integration/project_setup/test_association_status.py
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/contracts/test_plugin_manager_entry.py
Test: tests/contracts/test_skill_entrypoints.py

## R22: Uniform generator operations

Status: confirmed
Acceptance: The generator CLI skills/_shared/scripts/workflows.py has exactly the operations `create --kind marketplace|plugin` and `associate`. The former subcommands marketplace-create, plugin-create and configure do not exist and are invalid calls (exit 2, no alias, nothing written). `create` requires a known `--kind`; arguments of the other kind (kind marketplace: --marketplace, --skeleton, --description, --author, --languages, --default-language, --license, --license-file, --copyright-year, --copyright-holder; kind plugin: --owner, and --marketplace is required) are invalid calls before any write (exit 2). The answers name their operation in `action`: create-marketplace, create-plugin, associate. The Python operations are create_marketplace, create_plugin and associate. Test groups and test folder names keep their historical names (plugin-create, plugin_create, marketplace_create); they name test areas, not operations. Source/test names in this document that mention an operation use the new names.
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/flows/configure.md
Source: skills/setup/flows/marketplace.md
Test: tests/integration/plugin_create/test_create_cli.py

## R23: Skill set of the Manager: setup, docs, modify, verify, publish

Status: confirmed
Acceptance: The Manager offers exactly five public skills, each invoked as `/plugin-manager:<skill>`; the call selects the instructions, no first-argument routing exists. The former skills `plugin-manager` and `update` and the commands plugin-verify and marketplace-verify do not exist (R1, no alias). A skill never performs the task of another one. The kind (plugin or marketplace) is never a call argument: `setup` asks it once (R17), `docs` and `publish` read it from the configuration evidence (R15), `verify` detects it (`--kind auto`, ambiguous roots are rejected) and accepts an explicit `--kind`.
- `setup`: the state-guided skill (R11, R12, R17, R18, R21). It is the only skill that brings a repository into the configured state: operator language, configuration, skeleton, template sync, marketplace association. It may be called repeatedly; on a configured and synchronous repository it only prints the ready line (R18).
- `docs`: creates and refreshes README and docs/<language>/ from the actual sources in the repository-selected languages (R4); invents no capabilities or test results and preserves existing user prose. It places and links only screenshots the person supplied or authorized and does not generate screenshots.
- `modify`: changes name, display name and description of a plugin or marketplace (R24).
- `verify`: read-only structural verification and the explicit `--review` scope/source comparison; no writing helper, no target code execution. A passed check is no product acceptance.
- `publish`: approval-gated publication (diff, commit message, PR); never without concrete approval.
- State rule: every skill first runs the read-only `status`. `setup` runs the open flow. `docs` and `modify` stop with the reason and a pointer to `/plugin-manager:setup` when `next` is not `ready`, and write nothing; `publish` stops in the same way before preparation. The stop message of `docs`, `modify` and `publish` follows the mandatory layout of R25 (running text: "The <action> action was stopped, because this folder is not set up yet or only partly (<plain reason>).", a blank line, "Please run `/plugin-manager:setup` first."), delivered by `gate` as `message` and written unchanged, then, when the host offers a structured question tool, one question with two answers (run `/plugin-manager:setup` now: yes or no); on yes the skill hands over to `setup` and ends, on no or without an answer it ends, and it never runs a setup flow itself; the message is written in the language of the person's text in that call (labels and sentences translated) and in English for a bare command; it stores nothing, asks nothing and never guesses a language (the operator language stays with `setup`, R9/R10). `verify` continues and reports a pending setup or sync as a finding. Only `setup` writes the configuration evidence, skeleton files and sync decisions.
- The five skill descriptions name their task and boundary; `setup` states that it brings a repository up to date and may be called repeatedly.
- Generated plugins receive no setup flow and no setup_state.py; each plugin defines its own skills.
Evidence pending: the behavior of `/plugin-manager:<skill>` with several skills on Codex and Claude Code is unverified and needs a behavior test.
Source: skills/setup/SKILL.md
Source: skills/docs/SKILL.md
Source: skills/modify/SKILL.md
Source: skills/verify/SKILL.md
Source: skills/publish/SKILL.md
Source: skills/_shared/flows/gate.md
Source: skills/setup/scripts/setup_state.py
Test: tests/contracts/test_skill_set.py
Test: tests/contracts/test_plugin_manager_entry.py
Test: tests/integration/project_setup/test_gate.py
Test: tests/integration/plugin_create/test_no_entry_delivery.py

## R24: Skill modify

Status: confirmed
Acceptance: `/plugin-manager:modify` (a `--dry-run` shows the consequences and writes nothing) changes what a plugin or marketplace repository states about itself. The kind comes from the configuration evidence (R15), never from the call. Like `docs` it first passes the gate of R23 and stops with the reason and a pointer to `/plugin-manager:setup` when the workpackage is not ready, writing nothing then. The dialogue asks what to change (name, display name, description), shows the consequences before any write and writes only after the person's explicit yes; the helper takes explicit parameters (`--name`, `--display-name`, `--description`), validates them (technical name in lowercase kebab-case, display name and description not empty) and changes nothing when the values already match.
- Plugin: `name`, display name (`extensions.com.openai.interface.displayName`) and `description` of plugin.json; the derived host manifests are regenerated and, on a rename, `artifact` in config.json follows. The catalog entry of the plugin in its marketplace is updated in the same rollback-capable transaction when the checkout named by the ignored local.json is available (R21); otherwise the answer reports `catalog_entry_remains: true` with the values to change there. The repository name and URL stay. A name already registered in the marketplace for another repository is refused before any write.
- Marketplace: `name` and display name of marketplace.json with the derived host catalogs. The answer lists the plugin checkouts known from its ignored .local/marketplace.json (name, path) as affected plugins; modify never writes into them. A plugin repository takes the new marketplace name through `associate`, which treats the same checkout under a new name as an identity update of the same marketplace (config.json identity only, no catalog change; R21).
- The answer has `action: "modify"`, the kind, `changed`, `from`, `to`, `published: false`, `catalog_entry_remains` and `affected_plugins`, plus the follow-ups for the person: call forms (`/<name>:<skill>`, `<name>@<marketplace>`) and documentation are refreshed through `/plugin-manager:docs`; the changed files are committed files left unversioned and are published through publish. modify never commits, pushes, installs or publishes.
- Not part: keywords, category, icon, default prompts, owner, the repository URL, rewriting documentation or tests, and the marketplace association (stays in `setup`). With `modify` the Manager has five public skills (R23).
Source: skills/modify/SKILL.md
Source: skills/modify/scripts/modify.py
Source: skills/_shared/scripts/workflows.py
Test: tests/integration/modify/test_modify.py
Test: tests/contracts/test_skill_set.py

## R25: Messages to the person are plain

Status: confirmed
Acceptance: Every error message the Manager skills show has the same mandatory layout: two short paragraphs of running text without labels or list letters. The first says what could not be completed and why ("The <action> could not be completed, because <cause in plain words, the folder or file named by path>.") and, in one short sentence, what was already changed or that nothing was. The second, after one blank line, asks for the fix ("Please ..."; German: singular imperative), with at most two ways in one sentence ("either ... or ..."), exact commands and where to run them (for example in an IDE such as VS Code or in a terminal), and ends with the call to repeat. The message is written as the reply itself, never only in a status or summary field of the host. Labels and sentences are translated into the person's language (German: "..., weil ...", "Bitte ..."). No exit codes, JSON field names, script, helper or generator names, no words such as schema, evidence, hash, lock, transaction or migration, no raw error text; details only when the person asks. Known causes (no Git repository, no GitHub address, a folder inside another repository, an address that is not a plain GitHub address, Git not installed, a folder that is no marketplace, other content in the folder, existing files that differ, an unsupported file format) use the wording of one catalogue. A cause that is not in the catalogue is not guessed: the cause is stated as not known and what was or was not changed, the solutions are to call the same skill again and to run `/plugin-manager:verify`, and, when the host offers a structured question tool, one question offers to show the technical details (shown once, as quoted technical text, on yes); no repair command is run and nothing is retried silently. The layout and the wording come from the module of R26; `skills/_shared/references/messages.md` holds the rules for the model, every skill and failure flow points to it, and the gate stop (R23) uses the same layout. The helper errors a person can reach through a skill (a folder that is no Git repository, a plugin folder without a GitHub address, a folder inside another repository, an address that is not a plain GitHub address) name the command to run and carry no tool output.
Source: skills/_shared/references/messages.md
Source: skills/_shared/scripts/workflows.py
Source: skills/setup/scripts/state/reporting.py
Test: tests/contracts/test_skill_set.py
Test: tests/integration/plugin_create/test_git_messages.py
Test: tests/integration/project_setup/test_gate.py
Test: tests/unit/behavior/test_skill_cases.py


## R26: Failures become their message in Python

Status: confirmed
Acceptance: A failure is turned into the message the person sees by one module (`messages.py`), not by the model. Scripts raise failures with a catalogue code and the facts of the wording (path, address); the helper answer or the command line prints the finished message, in the language of the person (the language passed with `--message-language`, else the saved operator language, else English), in the layout of R25, in German and English from one catalogue; the model writes it unchanged and never composes, translates, shortens or extends it. The catalogue holds the known causes (no Git, a plugin folder without Git or GitHub address with both steps in one message, no GitHub address, a folder inside another repository, an address that is not plain or differs, other content, differing files, an unsupported format, not configured, invalid input of `modify`) and the closed gate. A failure without a catalogue code, an error of the host or a crash gets the same layout with "the cause is not known" through `setup_state.py explain`; the raw text stays technical detail, shown only on request. A new cause is a new catalogue entry with a code, never a sentence in a flow. Tests check that every catalogue entry has the layout in both languages without technical words, that every code the scripts raise is in the catalogue, that no other place builds the layout, and that the commands print the finished message. The model cases check whether the model passes the finished message on as it is; a single run shows that the text steers a model, never a frequency.
Source: skills/setup/scripts/state/messages.py
Source: skills/setup/scripts/state/cli.py
Source: skills/_shared/scripts/workflows.py
Source: skills/modify/scripts/modify.py
Source: skills/_shared/references/messages.md
Source: skills/_shared/flows/gate.md
Test: tests/unit/messages/test_messages.py
Test: tests/integration/plugin_create/test_prerequisites.py
Test: tests/integration/project_setup/test_gate.py
Test: tests/unit/behavior/test_skill_cases.py

## R27: One set of standards for every plugin

Status: confirmed
Acceptance: Every plugin repository carries the same four standards under `docs/standards/` (`coding.md`, `messages.md`, `testing.md`, `skills.md`), delivered and kept current by the Manager as managed files (sync, per-file decision on a deviation as for every managed file), and read by the agent before implementing: the managed `AGENTS.md` (R28) tells to read them and imports them for Claude Code. The standards are identical in every plugin and have no plugin-specific exceptions; a deviation is a finding, never an accepted state. `SCOPE.md` of a plugin holds only the goal and requirements of that plugin and never copies a standard; when it contradicts a standard, the standard wins. `verify` reports read-only, as a structural error: a missing or changed standard, and standard text copied into `SCOPE.md` or `CUSTOM.AGENTS.md`. `verify --review` additionally compares SCOPE and source with the standards and reports contradictions as findings with the standard, path and line; it never changes a standard or SCOPE. The standards cover coding (layout, context instead of globals, current formats only, coded failures), messages (layout, address, one catalogue built in code, R25/R26), tests (structure, rules, model tests, reporting) and skills (one skill per action, boundaries as structure, shared gate). Marketplace repositories receive no standards. The Manager is a plugin and follows the same standards (its own copies equal the managed files). A check of source against the standards that cannot be decided by reading (for example whether a message is built in a second place) remains the task of the review.
Source: skills/_shared/templates/plugin/sync/docs/standards/coding.md
Source: skills/_shared/templates/plugin/sync/docs/standards/messages.md
Source: skills/_shared/templates/plugin/sync/docs/standards/testing.md
Source: skills/_shared/templates/plugin/sync/docs/standards/skills.md
Source: skills/_shared/templates/plugin/sync/AGENTS.md
Source: skills/_shared/manifests/plugin.sync.json
Source: skills/_shared/scripts/verify.py
Source: skills/_shared/scripts/plugin_audit.py
Source: skills/_shared/references/scope-review.md
Test: tests/contracts/verify/test_standards.py
Test: tests/integration/project_setup/test_manifest.py
Test: tests/integration/project_setup/test_setup.py

## R28: Common agent instructions are managed, plugin-specific ones are the plugin's

Status: confirmed
Acceptance: Every plugin repository has two instruction files with separate owners. `AGENTS.md` carries the rules common to all plugins (scope first, current formats only, operator language, read the standards, read `CUSTOM.AGENTS.md`); the Manager delivers it as a managed file and keeps it current (sync, per-file decision on a deviation as for every managed file), and it is identical in every plugin. `CUSTOM.AGENTS.md` holds only what is specific to the plugin; the generator seeds it once, the Manager never manages, overwrites or deletes it, and it never repeats or weakens `AGENTS.md` or a standard. For Claude Code, `AGENTS.md` imports `CUSTOM.AGENTS.md` and the four standards, and `CLAUDE.md` stays limited to importing `AGENTS.md`; other hosts read the named files as text. `verify` reports, read-only, a missing or changed `AGENTS.md` and standard text copied into `CUSTOM.AGENTS.md`. A missing `CUSTOM.AGENTS.md` is not an error. Whether `CUSTOM.AGENTS.md` weakens a rule is a task of `verify --review`. Marketplace repositories are not part of this requirement. An existing plugin whose `AGENTS.md` differs gets the per-file decision of `setup`; the Manager converts nothing silently.
Source: skills/_shared/templates/plugin/sync/AGENTS.md
Source: skills/_shared/templates/plugin/seed/CUSTOM.AGENTS.md
Source: skills/_shared/templates/plugin/sync/CLAUDE.md
Source: skills/_shared/manifests/plugin.sync.json
Source: skills/_shared/scripts/verify.py
Source: skills/_shared/scripts/plugin_audit.py
Test: tests/contracts/verify/test_standards.py
Test: tests/integration/project_setup/test_manifest.py
Test: tests/integration/project_setup/test_setup.py
Test: tests/integration/project_setup/test_sync.py

## R29: Documentation reads every skill of the plugin

Status: confirmed
Acceptance: The documentation of a plugin repository is written from all of its sources, not from one skill: every skill under `skills/` (`SKILL.md` and its `references`, `flows` and `scripts`) and `SCOPE.md`, plus the `extra_sources` named in `docs/documentation.json`. `docs/documentation.json` holds only the language policy, `extra_sources` and open questions; it names no skill. A manifest with the field `source_skill` is rejected with a concrete reason before any write and is never converted or edited by the Manager. A standalone skill folder outside a repository is still documented as that one skill, with the output repository named explicitly. The documentation reads sources only and never executes them; the helper lists the sources (`inspect`), the agent reads them and writes the content from evidence.
Source: skills/_shared/scripts/documentation.py
Source: skills/_shared/WORKFLOWS.md
Source: skills/_shared/references/source-of-truth.md
Test: tests/integration/update/test_documentation.py
Test: tests/contracts/test_skill_entrypoints.py

## R30: Shared failure messages for plugins

Status: confirmed
Acceptance: Every plugin receives, as managed files, the module `skills/_shared/scripts/messages_base.py` and a language helper whose failures carry codes. `messages_base.py` is the only place that builds the layout of a failure message (R25/R26) and holds the layout in German and English, the failure class with a code and facts, the language choice (anything but German or English falls back to English), the name of the running plugin read from its `plugin.json` (never a constant) the command frame `run` that every skill script uses (it parses the call, turns a bad call into `ARGS_INVALID`, prints a failure as its finished message and reports anything else as not known, never raw text or a traceback) and a base catalogue with the failures every plugin has: the failures of the language helper (invalid tag, missing project folder, a link in the path, a path that is no folder, an unsupported saved setting), invalid call arguments and the "not known" failure. A plugin extends the base catalogue with its own entries in its own module and never builds the layout again. `operator_language.py` raises failures with the codes of that catalogue and its command line prints the finished message (options `--skill` and `--message-language`), never raw error text or a traceback; its other behavior is unchanged. The Manager ships byte-identical copies of both files. The standards (`coding.md`, `messages.md`) state these rules; whether a plugin follows them beyond what `verify` can read is a task of `verify --review`.
Source: skills/_shared/templates/plugin/sync/skills/_shared/scripts/messages_base.py
Source: skills/_shared/templates/plugin/sync/skills/_shared/scripts/operator_language.py
Source: skills/_shared/templates/plugin/sync/docs/standards/coding.md
Source: skills/_shared/templates/plugin/sync/docs/standards/messages.md
Source: skills/_shared/templates/plugin/sync/skills/_shared/references/operator-language.md
Test: tests/unit/messages/test_messages_base.py
Test: tests/integration/operator_language/test_cli.py
Test: tests/unit/operator_language/test_validation.py

## R31: A managed runner for model cases in every plugin

Status: confirmed
Acceptance: Every plugin receives the runner `tests/behavior/run_cases.py` as a managed file, identical everywhere. It reads the cases of the plugin from `tests/fixtures/skills/cases.json` (owned by the plugin; without the file it reports `NOT RUN` and exits 0) and, only when started explicitly with `--cli claude|codex` (`make test-behavior CLI=...` of a new plugin), sends each case to the model without tools: the real skill texts, the output of the commands the skill starts with and the conversation so far. The answer (reply, commands, next step, offered options, whether files are written) is graded deterministically against the expectation of the case: language, required and forbidden text, order, forbidden and required commands, next step, options, writes, number of questions. `--list` lists the cases without a model. The runner never installs a tool, starts no host and states that one run on one model shows that the text steers a model, not how often. `verify` does not run it; the standards (`testing.md`) require a case for every rule a model must follow.
Source: skills/_shared/templates/plugin/sync/tests/behavior/run_cases.py
Source: skills/_shared/templates/plugin/seed/Makefile
Source: skills/_shared/templates/plugin/sync/docs/standards/testing.md
Test: tests/unit/behavior/test_run_cases.py
Test: tests/integration/project_setup/test_manifest.py
