# Publish with approval

## Prepare

Ask the Manager to prepare publication for this repository. It reviews changes and destination, proposes a commit message, and prepares PR text, explicit files and checks. No commit, push or PR occurs before approval. A changelog can record dated changes but is not mandatory.

## Approve

Review the diff, message, repository, branch and merge method. An example request is: “May I create the named feature branch, commit the selected changes on it with the shown message, push, create the PR and merge after passing checks and required reviews?” This is an example, not a current approval request. Partial approval permits only the named steps.

## Execute and resume

The host performs Git/GitHub operations; the local helper records the plan, approval and observed stages and uses start-branch only to set up the approved local feature branch. In PR mode, publication ends at the observed merge. No version selection, tags, releases or plugin ZIPs. Errors preserve the reached state; changed content needs fresh review and approval. Journals stay outside source and installation. Old release journals cannot resume in the new workflow.

## Limits

GitHub access and suitable host tools are needed. GitLab MRs are not integrated. Branch rules and required reviews remain binding. Publish the separate plugin first and its marketplace entry afterwards; existing users may need to sync. The full live publication workflow has not been separately accepted.

[Usage](skills.md#publish) · [Installation](installation.md)

Plugin and marketplace use separate plans and journals. New or retargeted external sources require `dependencies` in the marketplace plan with observed repository URL, full commit hash and evidence. Failed plugin publication blocks dependent marketplace publication. The helper validates evidence fields; the agent must verify actual GitHub state.

## First publication without HEAD

Plugin and marketplace repositories support explicitly selected `publication_mode: "initial"`. It requires an unborn local HEAD and an observed empty remote with no branch heads. The concrete plan includes selected files, exact first commit message, confirmed default branch, repository, checks and `remote_empty_evidence`. Consent must explicitly cover the first commit and direct push without a PR; `--confirm-initial-publication` is additionally required. Preparation and approval themselves never create a commit.

After approval, recheck empty remote state and branch rules, create the first commit, push without force and verify actual remote content. The terminal stage is `published`. If a base branch is required or rules forbid the direct push, stop; never make an unsolicited seed commit. Normal PR plans require `base_commit` and `base_evidence` for an existing remote base branch. Subsequent changes use the PR workflow.

Schema-4 journals also bind presence and content of `.codex-plugin/plugin.json`. Addition, modification or removal invalidates approval even outside selected files. Schema-1/2/3 journals require a new plan and approval.

## Regular feature branch and permissions

Preparation → concrete approval → branch → commit → push → PR → checks → merge. The Manager proposes a descriptive name such as `improve-marketplace-setup`, without claude/ or codex/. The plan binds that name and the observed `default_branch`; default/base branches cannot be the feature branch. Only after approval does `start-branch` create the branch. On resume, reuse the same verified journal-owned branch; collisions, missing branches or changed heads stop the workflow. `check-before-commit` requires the approved active branch. Separately approved bootstrap remains the only exception for completely empty repositories.

Management tools require Git and Python 3.10+; Make is only a convenience wrapper. Management needs the selected host CLI only for automatic local installation/updates; explicitly requested model tests also need an authenticated CLI. Publish uses a sufficiently capable GitHub connector or alternatively authenticated gh; no GitLab MRs. First verify remote read, push, PR create/read, checks, rules and controlled merge capabilities and permissions. Report missing capabilities specifically; never install tools automatically. No additional Python packages, release Actions or version/tag requirements.

The plan includes `provider` and evidence in `capabilities`; the helper names missing capabilities individually. The agent verifies actual permissions and tools without test writes. [Canonical prerequisites](../../skills/_shared/references/prerequisites.md).
