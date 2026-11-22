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
Source: skills/plugin-create/SKILL.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R4: Complete skeleton documentation and report creation checks

Status: confirmed
Acceptance: New skeleton documentation contains localized, evidence-based scaffold content without unresolved placeholders for every selected language. No domain capabilities or test success are invented. Existing user prose is preserved and its validation failures remain visible. Creation checks actual plugin and marketplace structure and documentation, reports their results separately from licensing, pending functional acceptance and unexecuted tests/host checks, and does not claim completion on failed checks.
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/templates/skeleton-content.json
Source: skills/plugin-create/SKILL.md
Test: tests/integration/plugin_create/test_workflows.py

## R3: Separate conversation language from documentation language

Status: confirmed
Acceptance: plugin-create uses the language of the current user message for its interaction. With a bare slash command it uses the established conversation language; without either signal it asks briefly. Documentation languages are resolved independently and never determine the conversation language implicitly.
Source: skills/plugin-create/SKILL.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R5: Guided plugin-create dialogue

Status: confirmed
Acceptance: Missing setup inputs are collected using the host's available structured question tool in small coherent groups. Unknown conversation language is asked alone first and the agent waits before continuing in that language. Confirmed inputs are not asked again. When no structured tool is available, the agent explains this limitation and asks one concise question at a time in chat instead of dumping a questionnaire. No target writes occur while required answers are missing.
Source: skills/plugin-create/SKILL.md
Source: skills/_shared/references/workflows.md
Test: tests/behavior/plugin_create_acceptance.md

## R6: Implement confirmed licensing and persist the decision

Status: confirmed
Acceptance: plugin-create requires an explicit license identifier or explicit deferral before writes. A selected MIT license creates the standard license with confirmed copyright year and holder; another selected license uses an explicitly confirmed complete file without alteration. Missing inputs, unsupported templates and conflicting existing license files fail before plugin/marketplace writes. Existing matching license bytes are preserved. Selected licensing appears in plugin and derived host manifests, and new documentation in every selected language links to the persisted decision and license file. Explicit deferral is persisted without claiming a license. Final checks distinguish implemented, deferred and inconsistent licensing; existing prose is preserved and missing licensing documentation is reported.
Source: skills/_shared/scripts/licensing.py
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/templates/licenses/MIT.txt
Source: skills/plugin-create/SKILL.md
Test: tests/integration/plugin_create/test_licensing.py

## R7: Repeated creation detects existing products before license validation

Status: confirmed
Acceptance: An existing target product is rejected before licensing validation or creation writes, even with missing/conflicting licensing arguments. Unknown conversation language is resolved alone before offering existing-plugin actions; known language is used exclusively. The existing-plugin dialog offers only verification and configuration; it does not offer creation of another plugin or request another target path. Existing files and marketplace entries remain unchanged.
Source: skills/_shared/scripts/workflows.py
Source: skills/plugin-create/SKILL.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R8: Skeleton-only plugin creation

Status: confirmed
Acceptance: plugin-create creates only a new nonfunctional skeleton. Its dialogue offers no skill import or mode choice and requests no source skill path. The public helper rejects --source and --import before writes, including when combined with --skeleton. Other actions retain their own source-reading options. Existing source directories and target/marketplace data remain unchanged on rejected import calls.
Source: skills/_shared/scripts/workflows.py
Source: skills/plugin-create/SKILL.md
Source: skills/_shared/references/workflows.md
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/behavior/plugin_create_acceptance.md

## R9: Project-scoped operator language for generated plugins

Status: confirmed
Acceptance: Every newly generated plugin ships a shared operator-language helper and entry-point instructions. Before setup/domain interaction, a missing project preference is asked alone and persisted only after an explicit answer. Later calls reuse it, including bare slash commands and new sessions. An explicit change updates only that project's preference. Content/documentation languages remain independent; invalid state is rejected without mutation. Future skills preserve the same gate.
Source: skills/_shared/templates/plugin/skills/_shared/scripts/operator_language.py
Source: skills/_shared/templates/plugin/skills/_shared/references/operator-language.md
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
Acceptance: The central skill plugin-manager, for an explicitly selected standalone plugin repository (canonical plugin.json; never a marketplace or the embedded Manager), checks operator language and a closed list of shared development files without writes, stops on technical conflicts before any write, asks for a missing language, then adds only missing files/folders from the generator template, ensures the exact ignore rule /.project/operator.json before the first language write, stores the language through operator_language.py and records, per verified path, the pair {source_hash, local_hash} of full SHA-256 hashes in .project/plugin.skeleton.lock.json (schema_version 2, the only supported format: an older, unknown or invalid lock is rejected before writes and left unchanged, never migrated). The skeleton setup copies missing files and corrects missing or stale pairs of template-identical files; it never changes the bytes of an existing file. Existing files that differ are only changed by the explicit sync decision of R12; the only other files setup may modify are .gitignore (adding the exact rule) and .project/operator.json, each as specified. Technical errors (symlink, wrong type, unreadable, filesystem errors) are reported as such, never as content deviations, and stop further writes while actual partial changes stay listed. Concrete read-only requests only run the status. No Git, installation, network or target code. Other plugins and host activation by slash command are not part of this requirement; updating and removing existing files is governed only by R12.
Source: skills/_shared/scripts/project_setup.py
Source: skills/plugin-manager/SKILL.md
Test: tests/integration/project_setup/test_setup.py
Test: tests/contracts/test_plugin_manager_entry.py

## R12: Central entry dispatches by state: language, skeleton, configuration

Status: confirmed
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
Source: skills/_shared/templates/plugin/CLAUDE.md
Source: skills/_shared/scripts/project_setup.py
Test: tests/integration/project_setup/test_setup.py
