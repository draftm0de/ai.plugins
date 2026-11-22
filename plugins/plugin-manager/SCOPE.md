# Current-format policy / Aktuelle Formate

Status: confirmed

This scope records the approved compatibility boundary and creation interaction requirements, not a complete product acceptance.

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
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R4: Complete skeleton documentation and report creation checks

Status: confirmed
Acceptance: New skeleton documentation contains localized, evidence-based scaffold content without unresolved placeholders for every selected language. No domain capabilities or test success are invented. Existing user prose is preserved and its validation failures remain visible. Creation checks actual plugin and marketplace structure and documentation, reports their results separately from licensing, pending functional acceptance and unexecuted tests/host checks, and does not claim completion on failed checks.
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/templates/skeleton-docs
Source: skills/plugin-manager/flows/configure.md
Test: tests/integration/plugin_create/test_workflows.py

## R3: Separate conversation language from documentation language

Status: confirmed
Acceptance: Creation through the central plugin-manager entry uses the project-scoped operator-language gate of R12/R14. Documentation languages are resolved independently and never determine the operator language implicitly. The former standalone plugin-create entry is removed.
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R5: Guided plugin-create dialogue

Status: confirmed
Acceptance: Missing setup inputs are collected using the host's available structured question tool in small coherent groups. Unknown conversation language is asked alone first and the agent waits before continuing in that language. Confirmed inputs are not asked again. When no structured tool is available, the agent explains this limitation and asks one concise question at a time in chat instead of dumping a questionnaire. No target writes occur while required answers are missing.
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R6: Implement confirmed licensing and persist the decision

Status: confirmed
Acceptance: plugin-create requires an explicit license identifier or explicit deferral before writes. A selected MIT license creates the standard license with confirmed copyright year and holder; another selected license uses an explicitly confirmed complete file without alteration. Missing inputs, unsupported templates and conflicting existing license files fail before plugin/marketplace writes. Existing matching license bytes are preserved. Selected licensing appears in plugin and derived host manifests, and new documentation in every selected language links to the persisted decision and license file. Explicit deferral is persisted without claiming a license. Final checks distinguish implemented, deferred and inconsistent licensing; existing prose is preserved and missing licensing documentation is reported.
Source: skills/_shared/scripts/licensing.py
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/templates/licenses/MIT.txt
Source: skills/plugin-manager/flows/configure.md
Test: tests/integration/plugin_create/test_licensing.py

## R7: Repeated creation detects existing products before license validation

Status: confirmed
Acceptance: An existing target product is rejected before licensing validation or creation writes, even with missing/conflicting licensing arguments. Unknown conversation language is resolved alone before offering existing-plugin actions; known language is used exclusively. The central entry does not recreate an existing plugin; after language/skeleton handling it reports ready and waits under R12/R14. The former standalone existing-plugin action dialog is removed. Existing files and marketplace entries remain unchanged.
Source: skills/_shared/scripts/workflows.py
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R8: Skeleton-only plugin creation

Status: confirmed
Acceptance: plugin-create creates only a new nonfunctional skeleton. Its dialogue offers no skill import or mode choice and requests no source skill path. The public helper rejects --source and --import before writes, including when combined with --skeleton. Other actions retain their own source-reading options. Existing source directories and target/marketplace data remain unchanged on rejected import calls.
Source: skills/_shared/scripts/workflows.py
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R9: Project-scoped operator language for generated plugins

Status: confirmed
Acceptance: Every newly generated plugin ships a shared operator-language helper and entry-point instructions. Before setup/domain interaction, a missing project preference is asked alone and persisted only after an explicit answer. Later calls reuse it, including bare slash commands and new sessions. An explicit change updates only that project's preference. Content/documentation languages remain independent; invalid state is rejected without mutation. Future skills preserve the same gate.
Source: skills/_shared/templates/plugin/sync/skills/_shared/scripts/operator_language.py
Source: skills/_shared/templates/plugin/sync/skills/_shared/references/operator-language.md
Source: skills/_shared/scripts/workflows.py
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/operator_language_acceptance.md

## R10: Manager copy and delivery of the operator-language building block

Status: confirmed
Acceptance: The generator template remains the canonical source of the operator-language helper and reference; the Manager ships byte-identical standalone copies under skills/_shared/ as a delivery requirement. Their only Manager use is the central setup entry, which is separately authorized by R11; no other workflow uses them. The plugin generator template ignores exactly /.project/operator.json (no blanket .project/ rule, no duplicates); only newly created plugin repositories receive it, while marketplace repositories and existing plugins configured later keep their .gitignore. plugin-create ships helper and reference, never runs the helper and stores no preference. The helper does not edit .gitignore. Entry-point use (only R11's setup entry), skeleton sync and adoption by other plugins are not part of this requirement.
Source: skills/_shared/scripts/operator_language.py
Source: skills/_shared/references/operator-language.md
Source: skills/_shared/scripts/workflows.py
Test: tests/unit/operator_language/test_validation.py
Test: tests/integration/operator_language/test_cli.py
Test: tests/integration/plugin_create/test_operator_language_delivery.py

## R11: Central entry sets up operator language and missing shared development files

Status: confirmed
Superseded in part by R15-R18: configuration evidence, lock path, flow order and ready output are defined there; where they conflict, R15-R18 win.
Acceptance: The central skill plugin-manager, for an explicitly selected standalone plugin repository (canonical plugin.json; never a marketplace or the embedded Manager), checks operator language and a closed list of shared development files without writes, stops on technical conflicts before any write, asks for a missing language, then adds only missing files/folders from the generator template, ensures the exact ignore rule /.project/operator.json before the first language write, stores the language through operator_language.py and records, per verified path, the pair {source_hash, local_hash} of full SHA-256 hashes in .project/plugin.skeleton.lock.json (schema_version 2, the only supported format: an older, unknown or invalid lock is rejected before writes and left unchanged, never migrated). The skeleton setup copies missing files and corrects missing or stale pairs of template-identical files; it never changes the bytes of an existing file. Existing files that differ are only changed by the explicit sync decision of R12; the only other files setup may modify are .gitignore (adding the exact rule) and .project/operator.json, each as specified. Technical errors (symlink, wrong type, unreadable, filesystem errors) are reported as such, never as content deviations, and stop further writes while actual partial changes stay listed. Concrete read-only requests only run the status. No Git, installation, network or target code. Other plugins and host activation by slash command are not part of this requirement; updating and removing existing files is governed only by R12.
Source: skills/_shared/scripts/project_setup.py
Source: skills/plugin-manager/SKILL.md
Test: tests/integration/project_setup/test_setup.py
Test: tests/contracts/test_plugin_manager_entry.py

## R12: Central entry dispatches by state: language, skeleton, configuration

Status: confirmed
Superseded in part by R15-R18: configuration evidence, lock path, flow order and ready output are defined there; where they conflict, R15-R18 win.
Acceptance: /plugin-manager:plugin-manager reads a write-free status of an explicitly selected folder and runs exactly the needed flow, re-checking after every successfully completed flow. Priority: technical conflict (stop), operator language missing (language flow), skeleton additions or lock evidence missing (skeleton flow), a managed file needing a keep/adopt decision (sync flow), plugin.json missing (configuration flow), otherwise ready. The skeleton is the fixed list of nine managed files with parent folders, the ignore rule and lock evidence; it needs no plugin.json, Git, origin or marketplace and invents no identity. A folder without plugin.json is accepted when it holds only .git/.idea (checked as directories, never opened), a regular UTF-8 .gitignore, valid .project metadata and skeleton paths, including the entry's own earlier output; other content, an invalid plugin.json, a marketplace or the embedded Manager stop before writes. Sync rules per managed file: missing locally, copy from a valid source and record both hashes after verification; source and local identical, correct a missing or stale pair without a dialogue; source and local differ and the stored pair equals the current pair (source_hash and local_hash both), the deviation is accepted without dialogue or writes; source or local changed since the accepted pair (or no pair, or no lock) while contents differ, a decision is required and nothing is overwritten automatically. Status reports path, hashes, reason and decision need structurally and asks nothing; the skill shows only the file path and the fact that differences exist, without file contents, text excerpts, diffs or content summaries, and explicitly asks for "keep local file" or "adopt template" in the operator language. Keep leaves the local bytes and records both current hashes; adopt replaces only the explicitly selected file (mode kept), verifies it and records both hashes. Cancellation, silence or a preselection is no decision and persists nothing; a decision holds only for the shown pair and a changed pair stops for a new check. Removal rules for a managed path whose source was removed in the parent template (a single missing source of a listed path, while the template base exists and holds at least one managed source; a missing or invalid base, symlinks, wrong types and read errors are technical conflicts, never removal): the file is deleted automatically only if the lock proves ownership and the current local hash equals the stored local_hash and the stored source_hash; a changed or accepted local file always requires an explicit "keep local file" or "delete local file" question (no content, excerpt, diff or summary is shown, only the path and that the source was removed); without lock evidence nothing is deleted; a locally missing owned file only loses its lock entry; keep records source_hash null with the current local_hash (a documented extension of lock schema_version 2, set only by this decision), so an unchanged repetition does not ask again and a later local change does; a returning source is classified normally again. After removal only empty parent folders of the removed file go, bottom-up with rmdir, never needed skeleton folders, the project root, .git, .idea or .project, and foreign files are never deleted. Status reports automatic removals, questions, kept files, unowned files and lock cleanup separately, writes nothing, and the skeleton flow executes the automatic part. Folders are not hashed or moved, extra local files are kept, AGENTS.md is not managed and new managed files need an entry in the fixed list; a removed source stays recognizable only while its path remains in that list. For the explicitly requested manual sync test, keep.md and remove.md are in that list. Accepted deviations cause no sync routing and never mean matches_template; ready is not product acceptance. Configuration runs after language and skeleton in the same call and folder through the existing plugin-create generator and its rules, with inputs, GitHub origin and marketplace asked or reported as external prerequisites, never invented, rolled back or changed without explicit selection; a generator collision with a deviating or deliberately kept skeleton file changes nothing and stops openly, to be resolved only by the sync flow. Read-only requests run one status only. Errors and missing progress stop with concrete reasons and actual partial changes; ready waits for input. Dialogue and flow text is instruction evidence, not model or host behavior; concurrent writers are organizationally excluded.
Source: skills/_shared/scripts/project_setup.py
Source: skills/plugin-manager/SKILL.md
Source: skills/plugin-manager/flows/language.md
Source: skills/plugin-manager/flows/skeleton.md
Source: skills/plugin-manager/flows/configure.md
Source: skills/plugin-manager/flows/sync.md
Source: skills/plugin-manager/flows/skeleton.md
Test: tests/integration/project_setup/test_fresh.py
Test: tests/integration/project_setup/test_sync.py
Test: tests/integration/project_setup/test_removal.py
Test: tests/contracts/test_plugin_manager_entry.py

## R13: Managed Claude compatibility file

Status: confirmed
Acceptance: The plugin generator and central skeleton setup share a CLAUDE.md template containing only an English compatibility comment and @AGENTS.md. All agent instructions belong in AGENTS.md. Missing CLAUDE.md is copied and its hash pair recorded in the skeleton lock, identical content is preserved and recorded, and existing different content is preserved until an explicit sync decision (R12) keeps or replaces it; it is never overwritten automatically. A fresh folder containing this skeleton file remains initializable. AGENTS.md is not added to skeleton management.
Source: skills/_shared/templates/plugin/sync/CLAUDE.md
Source: skills/_shared/scripts/project_setup.py
Test: tests/integration/project_setup/test_setup.py
The same compatibility CLAUDE.md applies to every kind (plugin, marketplace) and to this repository itself; a differing "Project instructions" variant is not used.

## R14: Creation through the central Manager entry

Status: confirmed
Superseded in part by R15-R18: configuration evidence, lock path, flow order and ready output are defined there; where they conflict, R15-R18 win.
Acceptance: Plugin creation has no separate public plugin-create skill or command wrapper. The central plugin-manager configuration flow owns the guided creation instructions and uses the existing internal plugin-create --skeleton generator. Licensing, preservation and creation checks remain required. Existing marketplace associations are handled by the associate flow of R21 (the former configure skill is removed). Creation uses the saved operator-language gate of R12; former standalone entry dialogue rules do not create another public entry.
Source: skills/plugin-manager/flows/configure.md
Test: tests/contracts/test_skill_entrypoints.py
Test: tests/contracts/test_plugin_manager_entry.py

## R15: Workpackage configuration evidence per running plugin

Status: confirmed
Acceptance: Every plugin using the central entry keeps its configuration evidence in the workpackage under .project/plugins/<plugin>/config.json, where <plugin> is the name of the running plugin (for the Manager: plugin-manager), passed to the helper as --plugin. Format: {schema_version: 2, plugin, kind, artifact, configured_at, marketplace}; kind is a kind of the manifests (the Manager: plugin or marketplace); artifact is the name of the created plugin or marketplace; configured_at is an ISO-8601 UTC timestamp; marketplace is {name, repository} for a kind whose manifest says requires_marketplace (the Manager: plugin) and null for every other kind. The file is committed; schema_version 1 and a missing, partial or unexpected marketplace property are an unsupported format (conflict before any write, unchanged, no migration). A plugin belongs to exactly one marketplace, so its configuration is complete only with that identity (R21); ready therefore includes the association, without a further gate. The machine-specific path of that marketplace is never part of this file: it lives in the Git-ignored .project/plugins/<plugin>/local.json ({schema_version: 1, marketplace_path}, strictly validated). The file is written only after a successful configuration run (generator checks passed) and never earlier. A workpackage is configured for a plugin only if this file is valid; a root plugin.json or marketplace.json is a product, never evidence. Evidence of other plugins does not configure this one. Missing, unreadable, extra-key, wrong-type, unknown-kind or plugin-mismatching files are reported as conflicts before any write, leave all data unchanged and are never migrated. Status reports configuration {plugin, configured, kind}. The helper operation record writes the file only after a passed configuration run and, for a kind with requires_marketplace, only if local.json names a marketplace checkout whose marketplace.json lists the plugin (name and repository URL); it takes the identity {name, repository} from that checkout and otherwise refuses with association_missing ("associate first") without writing.
Source: skills/_shared/scripts/project_setup.py
Source: skills/plugin-manager/SKILL.md
Test: tests/integration/project_setup/test_workpackage_config.py

## R16: Skeleton per kind: sync/ and seed/ folders, generated hash file, manifest

Status: confirmed
Acceptance: Every kind has two template folders: skills/_shared/templates/<kind>/sync/<project path> (files kept in sync: copied 1:1, hashed in .project/plugins/<plugin>/skeleton.json, schema_version 2, and synchronized under the keep/adopt/delete rules of R12) and skills/_shared/templates/<kind>/seed/<project path> (files created once when missing, with a short intro of what the file is for, never what it does; never hashed or synced). The folder a file lies in is the only statement of its class. skills/_shared/manifests/<kind>.json is only {schema_version: 1, product, requires_marketplace, derived: [{path, generate, check}]} (product = root file naming the kind or null; requires_marketplace = boolean, true only for the Manager kind plugin; derived = catalogs produced by a named command of the kind and only verified by its check command, never copied or hashed). skills/_shared/manifests/<kind>.sync.json is generated, never edited by hand: {schema_version: 1, files: {<path>: {sha256, executable}}, removed: [<path>]}, sorted, with a trailing newline. files lists exactly the files of sync/ (full SHA-256 of the bytes, executable bit); removed lists tombstones, paths whose template source was removed in the parent (plugin: keep.md, remove.md), and may not overlap files. The development tool scripts/skeleton_hashes.py (make build-skeleton-hashes / check-skeleton-hashes) writes the file (build keeps removed) and verifies it (check exits 1 naming each path on a hash or executable mismatch, a missing or unlisted file, an invalid file or an overlap); check runs in both CI workflows of this repository, never in generated repositories. The helper trusts the file only as the expected value: before copying or comparing it hashes every source of sync/ and refuses with a template_base conflict (reason names make build-skeleton-hashes) on a deviating or missing source of a listed path, an unlisted file in sync/, an invalid sync file or an overlap, and writes nothing. The removal rules of R12 apply only to paths in removed. Templates and manifests carry -text in .gitattributes so line endings never change a hash. The kind marketplace has sync = CLAUDE.md and scripts/{local_plugins,marketplace,plugin_payload,run_tests,verify}.py; seed = Makefile (only install-local and test), AGENTS.md, SCOPE.md, docs/architecture.md, docs/prerequisites.md, local-marketplace.example.json, tests/README.md, tests/__init__.py, tests/contracts/__init__.py, tests/contracts/test_structure.py; derived = .claude-plugin/marketplace.json and .agents/plugins/marketplace.json (marketplace.py sync / check). The kind plugin has the nine files of R11 plus the shared helper and flows of R19 in sync/ and the generator files (AGENTS.md, SCOPE.md, CHANGELOG.md, Makefile, ci.yml, gitignore.txt, docs, tests) in seed/. The former .project/plugin.skeleton.lock.json is an unsupported format (no read, migration or deletion). The ignore rules written by the generators are /.project/operator.json (new plugin repositories only) and /.project/plugins/*/local.json (every plugin repository where the association is written; effectiveness is checked with Git before writing); the marketplace side keeps .local/.
Source: skills/_shared/scripts/project_setup.py
Source: scripts/skeleton_hashes.py
Source: skills/_shared/manifests/plugin.json
Source: skills/_shared/manifests/plugin.sync.json
Source: skills/_shared/manifests/marketplace.json
Source: skills/_shared/manifests/marketplace.sync.json
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/integration/project_setup/test_manifest.py
Test: tests/integration/project_setup/test_sync_files.py
Test: tests/unit/skeleton_hashes/test_skeleton_hashes.py
## R17: Dispatch order and kind selection

Status: confirmed
Acceptance: The status priority is: technical conflict (stop), operator language missing (language), workpackage not configured for the running plugin (configure), skeleton additions or evidence missing (skeleton), managed file needing a decision (sync), otherwise ready. The configure flow first asks "plugin or marketplace?" (explicit answer, no preselection); plugin starts the plugin setup flow, marketplace the marketplace flow (R20); an existing root plugin.json is named and stops the plugin branch. A marketplace.json in the root is no conflict once the kind is marketplace. The generator creates only product files and never touches, judges or fails on existing managed skeleton files; skeleton differences are resolved by the skeleton and sync flows after the configuration evidence exists. Flow success is re-checked by status; after configuration both the evidence of R15 and the skeleton files of the chosen kind exist.
Source: skills/_shared/scripts/project_setup.py
Source: skills/plugin-manager/SKILL.md
Source: skills/plugin-manager/flows/configure.md
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/contracts/test_plugin_manager_entry.py

## R18: Ready output

Status: confirmed
Acceptance: When status is ready, the entry outputs only the line "Plugin <name> Status: fully configured" in the operator language (German: "Plugin <name> Status: vollständig konfiguriert") and waits. Skeleton deviations and other details are not listed unless asked.
Source: skills/plugin-manager/SKILL.md
Test: tests/contracts/test_plugin_manager_entry.py

## R19: Identical flow in every generated plugin

Status: confirmed
Acceptance: A newly generated plugin ships the common part byte-identically: skills/_shared/scripts/project_setup.py and operator_language.py, and the flow texts entry, language, skeleton and sync under skills/_shared/flows/ (no plugin name inside; the name is the name of the plugin's central skill passed as --plugin). The custom part is only created: skills/<name>/SKILL.md (name, description and a short intro of its purpose) and skills/<name>/flows/configure.md (intro stub, no procedure), plus skills/_shared/manifests/default.json (product null, requires_marketplace false, no derived) and default.sync.json (empty files and removed). The helper reads its kinds from skills/_shared/manifests/*.json (the Manager: plugin and marketplace; a generated plugin: default); configuration evidence, ready line and flow order follow R15-R18 with the plugin's own name. Generation never overwrites existing files.
Source: skills/_shared/templates/plugin/sync/skills/_shared
Source: skills/_shared/scripts/workflows.py
Test: tests/integration/plugin_create/test_workflows.py

## R20: Marketplace setup is part of the central entry

Status: confirmed
Acceptance: The marketplace setup is a flow of the single plugin-manager skill; there is no skill skills/marketplace-create and no commands/marketplace-create.md. The complete procedure is skills/plugin-manager/flows/marketplace.md (no reference to a separate skill). flows/configure.md asks "Plugin or marketplace?" first (R17), holds the dialogue rules shared by both kinds (section "Guided dialogue (both kinds)") and hands over to flows/marketplace.md for the marketplace. The cloned marketplace folder is the working folder. Technical name (kebab-case), display name and owner/publisher are asked one at a time or in small coherent groups, never invented and never taken from the Git author; an existing marketplace.json supplies missing values and the origin supplies the repository URL (optionally checked against an explicit one). Nothing is written before the facts are answered. The helper call is workflows.py marketplace-create --root <folder> --name ... --display-name ... --owner ... [--repository ...]; success is exit 0 (the answer carries action, changed, repository and published: false, but no ok or checks), then record --kind marketplace --artifact <name> writes the configuration evidence, then status leads to the skeleton flow (hash evidence) and ready. Repeating the operation is idempotent; an identity conflict stops without writes; a plugin repository (plugin.json) is no marketplace. As in R17 the generator neither judges nor replaces an existing synced file listed in manifests/marketplace.sync.json (a deviating one stays byte-identical and surfaces as a sync decision afterwards); seed files never change existing files. The generated starter READMEs name only existing commands (python3 -B scripts/verify.py, python3 -B scripts/marketplace.py sync|check, make install-local), never removed make targets.
Source: skills/plugin-manager/flows/marketplace.md
Source: skills/plugin-manager/flows/configure.md
Source: skills/_shared/scripts/workflows.py
Test: tests/contracts/test_plugin_manager_entry.py
Test: tests/contracts/test_skill_entrypoints.py
Test: tests/integration/marketplace_create/test_workflows.py

## R21: Marketplace association is a flow of the single plugin-manager skill; a plugin belongs to exactly one marketplace

Status: confirmed
Acceptance: A plugin belongs to exactly one marketplace; that is a mandatory property of its configuration (R15): the committed config.json carries the identity {name, repository}, the Git-ignored .project/plugins/plugin-manager/local.json ({schema_version: 1, marketplace_path}, strict) the path of the checkout on this machine. The former plugin-side .local/marketplace.json (default marketplace and named associations) is neither written nor read, there is no fallback and no migration; the marketplace side keeps the checkouts of its plugins under sources in its own .local/marketplace.json. The association is the flow skills/plugin-manager/flows/associate.md; there is no skill skills/configure and no commands/configure.md, and the helper operation configure is replaced by workflows.py associate --root <plugin> --marketplace <local path of the target marketplace> [--plugin plugin-manager] [--repository URL] [--drop-missing-old]. associate requires the configuration evidence (schema 2) of a kind with requires_marketplace and a plugin.json whose name equals the artifact; it validates the target structurally as a marketplace (marketplace.json with name and repository at its root, no plugin.json, valid catalogs; no configuration evidence of the target is required), plugin and marketplace are separate repositories, the plugin identity must not belong to another repository, neither .local of the marketplace nor local.json of the plugin may be tracked and the ignore rules must be effective. The same marketplace (same name, same repository) is idempotent: a fresh clone or moved checkout only gets its local.json; the same name with another repository is an identity conflict. Changing to another marketplace writes in ONE rollback-capable transaction: entry and sources of the plugin in the new marketplace, removal of exactly this plugin's entry (matching name and repository URL) and of its sources mapping from the old marketplace, both host catalogs of both marketplaces regenerated, the identity in config.json and the path in local.json. The old marketplace is found through local.json and must carry the name of the identity; if it is not available locally the change is refused unless --drop-missing-old is given, which releases only the local reference and the identity and reports old_catalog_entry_remains: true because the committed catalog line of the old marketplace has to be removed there. The first association happens through plugin creation, which writes local.json and refuses an existing association to another marketplace ("use associate to change"). associate creates no development tools, never commits, pushes, installs or publishes; its answer has action, changed, from, to, published: false, old_catalog_entry_remains and a note that the changed files (config.json of the plugin, marketplace.json and host catalogs of the marketplaces involved) are committed files left unversioned and are published through publish. project_setup status reports for a kind with requires_marketplace the read-only field association {marketplace, path, state: ok|path_missing|path_invalid|mismatch|unsupported}; it never gates ready, never writes and treats a missing local.json (fresh clone) as a hint only. The entry routes a request to set, change or move the marketplace of a plugin, after the language gate, to the flow, which asks the local path of the target marketplace as an explicit choice (a suggestion is not a selection). The runtime of the plugin (install-local) and the read-only verification read the path only from local.json; their messages name the plugin-manager association instead of "configure". `install-local` knows no marketplace override (no `--marketplace` option, no `MARKETPLACE` make variable, no `marketplace_root` parameter); the marketplace comes only from `.project/plugins/plugin-manager/local.json`, and the existing check that the plugin is linked in that marketplace stays.
Source: skills/plugin-manager/flows/associate.md
Source: skills/plugin-manager/SKILL.md
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/scripts/project_setup.py
Test: tests/integration/associate/test_associate.py
Test: tests/integration/associate/test_workflows.py
Test: tests/integration/project_setup/test_association_status.py
Test: tests/integration/project_setup/test_workpackage_config.py
Test: tests/contracts/test_plugin_manager_entry.py
Test: tests/contracts/test_skill_entrypoints.py
