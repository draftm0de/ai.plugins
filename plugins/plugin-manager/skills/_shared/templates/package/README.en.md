# Plugin Manager

[Deutsch](README.md) | **English**

This plugin documents accessible local skills and plugins from source evidence. Documentation languages are chosen per repository: German only, English only or both. Use `marketplace-create` for a marketplace, `plugin-create` for a separate plugin, `configure` for its association, `update` to refresh documentation, or `verify` for a read-only structure audit. The agent asks about material uncertainties. Passing structural checks does not establish production readiness. Nothing is published or installed without instruction.

In Claude: `/plugin-manager:verify SOURCE_PATH`, with equivalent `:plugin-create` and `:update` commands. In ChatGPT request the action in natural language. The host must have access to the source; helpers require Python 3.10 or newer.

[Workflow and limitations](skills/_shared/WORKFLOWS.md)

## Publish with approval

`/plugin-manager:publish SOURCE` prepares the diff, commit message and PR. Approval covers feature-branch setup, commit, push, PR, checks and merge. No versions, tags or releases. Publish new plugin repositories before their marketplace entries. The journal helper performs no publication itself. [Workflow](skills/_shared/references/publish.md).

PRs require an observed existing base branch. An empty remote with unborn local HEAD needs a separate plan explicitly approving the first commit and direct push without a PR. Initial commits are never automatic. Schema-4 journals also bind Codex manifest modification, addition and removal outside selected files.

Management tools require Git and Python 3.10+; Make is only a convenience wrapper. Management needs the selected host CLI only for automatic local installation/updates; explicitly requested model tests also need an authenticated CLI. Publish uses a sufficiently capable GitHub connector or alternatively authenticated gh; no GitLab MRs. First verify remote read, push, PR create/read, checks, rules and controlled merge capabilities and permissions. Report missing capabilities specifically; never install tools automatically. No additional Python packages, release Actions or version/tag requirements.

Local snapshots read the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. Local tests require no commit, push or PR. Keep one shared `<marketplace-id>-dev`, with no additional marketplaces per branch.

`configure` is the normal setup path. `local-marketplace.example.json` is an optional manual copy template. Only `.local/marketplace.json` is read for local runtime mappings; never commit those mappings.

## Skills

`plugin-manager`, `marketplace-create`, `configure`, `verify`, `update` and `publish`. Shared rules: `skills/_shared/WORKFLOWS.md`; plugin-manager is the central entry.
