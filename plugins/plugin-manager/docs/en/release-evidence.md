# Verification evidence

## Current-format boundary (2026-11-19)

Only current rules apply: no obsolete-format support, fallback paths or automatic migration. Earlier entries below are historical evidence, not promises of current compatibility. Rejected user data remains unchanged.

## Scope/source review model evaluations (2026-11-19)

Six fictional cases were run with Claude Code 2.1.319 (usage metadata: claude-sonnet-5-5) and Codex CLI 0.165.0 (CLI default model; exact identity was not exposed in captured events). Both received the same review rules, complete fictional files and observed static reports; expected outcomes were withheld. Tools were disabled/restricted and source was never executed.

Initial automated scores were Claude 4/6 and Codex 6/6. Human review identified a conflation of source verdict and test coverage and an out-of-scope test edge case in Claude responses. The shared review contract was clarified. Two grader false positives (omitted quote indentation and describing an explicitly rejected success instruction) were corrected with regressions. Initial responses and original grading remain unchanged.

All responses from the complete repeat run were read manually and regraded with the corrected evaluator: **Claude 6/6, Codex 6/6**. Both correct plugins had no defect/test-gap false alarms; the real write defect, vacuous test and missing source were classified appropriately. No report claimed executed tests, runtime acceptance or publication readiness. The injected success instruction was ignored. All fictional target directories remained byte-identical.

[Versioned evidence](../../tests/behavior/evidence/review-models-2026-11-19.json). Raw responses, prompts and diagnostics remain separate in ignored .tmp directories. These 24 model calls (initial and repeat runs) are bounded prompt evaluations, not a statistical reliability guarantee or unrestricted host/tool acceptance. Text heuristics still need human review. No personal plugin installations changed; no commits or pushes.

## Skeleton and scope/source review (2026-11-19)

The evaluated version supported --skeleton and --source. Current plugin-create supports only --skeleton; the import mode has been removed. New scaffolds include draft SCOPE.md, AGENTS.md, CLAUDE.md and architecture rules. Verify reports skeleton status separately from structural validity and offers --review for static read-only evidence checks. Subsequent semantic agent comparison has its own report contract; available file pointers do not establish domain or test acceptance.

The complete deterministic run passed 146 tests (25 marketplace, 121 Manager); separately four native tests passed without skips in isolated Claude/Codex profiles. Targeted create and review tests also passed after final adjustments. Scenarios cover missing scope, draft requirements, safe evidence paths, skeletons, runtime dependencies on developer tools and unchanged source files. Deliberately contradictory source is never falsely certified by evidence collection. Model-based review evaluations were not run; clarification dialogs and semantic LLM reliability remain separate acceptance work. No personal installations changed; no commits or pushes.

## Unified test layout (2026-11-19)

All 212 existing test methods across marketplace, Manager and Coach are retained. Tests are grouped by type first, then by skill/component where useful. Four additional tests protect test selection; another checks Make test commands in newly generated repositories. `make test` passed 134 deterministic tests in ai.plugins including Manager and 79 in Coach. Separately, `make test-native` passed four tests in isolated Claude/Codex profiles, none skipped. Model tests were not run; Coach currently has no dedicated native suite. Earlier native flags on make test are historical commands; test-native is now the explicit entry point. No personal installations changed, no commits or pushes.

## Seven skills (2026-11-19)

The six public skills are marketplace-create, plugin-create, configure, verify, update and publish. Shared rules, helpers and templates remain bundled under skills/_shared, which has no SKILL.md. Onboarding points to the read-only verify skill. Explicit verification variants and init guidance remain commands.

The complete native test run passed 133 tests (23 marketplace, 110 Manager), none skipped. New regressions check the exact skill inventory, frontmatter, shared resources in both host payloads and command routing. Existing publication, ignore and Codex-manifest regressions still passed. Native tests used temporary repositories and isolated host profiles only. No personal installations changed; no commits, pushes or publication. GitHub/GUI acceptance remains separate.

## Documentation review on 2026-11-19

`update` reread the current sources of both repositories. German/English content, skill paths, configure setup, local snapshots, publication approval and historical evidence are aligned. Documentation validation, manifest/catalog checks, verify and local marketplace README links passed. Coach: 79 tests passed. ai.plugins including Manager: 130 tests collected, 126 passed and four optional native tests deliberately skipped. No new host/GUI test or model calls. No personal installations changed; no commits, pushes or publication.

## Confirmed observations

On 2026-11-18 the user reported successful imports in Claude and GPT. Local CLI imports had also been checked in isolated Claude and Codex profiles. The repository was available as `draftm0de/zyris.skill.manager` after commit `58edc2b`.

## Limits

This confirms initial import, not complete feature, update, uninstall or publication behavior. Record current local results in the relevant work report; do not reuse old test counts as evidence for new changes. Newly initialized plugins need their own host acceptance.

## Next host test

After a separately approved push, refresh the marketplace, open a new chat and verify the revised create/configure/verify/publish rules. Do not perform a production publication just to test them. Until that push these revised rules exist only locally.

[Installation](installation.md) · [Publish](publish.md)

## Local acceptance on 2026-11-19

The uncommitted working tree based on ai.plugins `65c1ecb` passed 112 tests (21 marketplace tests and 91 Manager tests), with none skipped, using:

```sh
PLUGIN_MANAGER_NATIVE=1 ZYRIS_TEST_SHARED_LOCAL=1 ZYRIS_TEST_LOCAL_NATIVE=1 make test
```

Coverage includes a new marketplace without an embedded Manager, a separate plugin, association of an existing plugin, retained associations and explicit local override, conflicts and symlinks, preserved unrelated content, and missing local configuration with valid publishable structure. A real Git clone against a temporary local fixture exercised a missing checkout; GitHub credentials and network access were not involved.

Native Claude/Codex tests used temporary profiles only. Both plugins were installed, edited without commits and updated; actually loaded skill files were compared with the working trees. The create workflow also ran from an isolated Manager copy outside the developer checkout. Publication tests checked separate marketplace plans, required plugin evidence and invalidated approvals without publishing.

`make check-plugin`, `make verify`, `make plugin-verify SOURCE=../ai.plugin.interview-coach`, `make validate-docs` and `git diff --check` passed. Both real repository structures and their existing local associations are valid; the Coach checkout remained unchanged at `edaf2d9`.

These observations establish local tooling/CLI acceptance. Publication of these changes, GitHub cloning with real credentials, subsequent GUI installation/update and a complete live publication remain untested. Generated documentation templates still need completion from confirmed product sources; license terms and skill behavior are never invented. Personal host installations were not used as test targets.

## Cross-review: targeted regressions

After the three fixes, 119 tests passed (21 marketplace and 98 Manager tests), none skipped, using the same complete native test command. First publication for plugins and marketplaces was exercised with actual first commits and pushes exclusively to temporary local bare repositories. Preparation and approval alone preserved HEAD and working files; missing initial consent and missing PR base were rejected.

Root and nested ignore negations were reproduced: configure/plugin-create stopped before changes and existing mappings remained byte-identical. Normally generated local configuration was effectively ignored by Git. Modification, addition and removal of the unselected Codex manifest invalidated approval. Schema-1/2 journals need a new plan. Metadata, structure, documentation and diff --check passed. No GitHub publication or changes to personal host installations; GitHub/GUI acceptance remains outstanding.

## Feature branch, prerequisites and local development

After the targeted refinement, 130 tests passed (23 marketplace and 107 Manager tests), none skipped, using the complete native test command above. Added regressions cover branch creation only after approval, neutral names, exclusion of default/base branches, name collisions, resumption including interrupted branch creation, and missing/changed branches. Default-branch commit evidence is rejected. Missing GitHub capabilities are reported specifically; bootstrap, effective ignore checks and Codex manifest binding remain covered.

Local snapshots were checked after branch switches and uncommitted edits using the same development marketplace. Direct Python snapshot and verify commands ran with an empty PATH without Make or a host CLI. A malformed optional example JSON did not affect runtime; missing .local configuration did not trigger an example-file fallback. Template copies of the central prerequisites were verified byte-identical.

Metadata, structural, documentation and diff --check validations passed. The working repository stayed on main at 65c1ecb; the Coach checkout was unchanged. Branch/commit/push operations occurred only in temporary test repositories; personal host installations were untouched. Schema-4 plans require new approval; actual GitHub connector/gh permissions and GitHub/GUI publication will be checked only during an explicitly requested publication run.
