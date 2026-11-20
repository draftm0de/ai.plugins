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
