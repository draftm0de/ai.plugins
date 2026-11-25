<!--
This file comes from the plugin manager and is managed by it: do not edit it here, changes are overwritten or reported.
Write your marketplace's own instructions in CUSTOM.AGENTS.md.
-->

# Development rules

Read SCOPE.md and docs/architecture.md before changing anything. Clarify missing or contradictory
requirements; never infer them from existing files. Preserve unrelated edits.

Use verify for read-only checks and its explicit --review mode for scope/source review. Do not execute target
code as part of review. Run tests only as a separately authorized development step and report actual results.
Do not change scope to hide implementation gaps. Never read private workspaces, credentials or ignored personal
data. Do not install tools, commit, push or publish without the corresponding authorization.

## Scope

`SCOPE.md` is managed by the plugin manager and identical in every marketplace, because every marketplace has the
same task: never edit it here and never deviate from it. Which plugins are listed is stated in `marketplace.json`.

## Marketplace-specific instructions

Also read `CUSTOM.AGENTS.md` when it exists. It holds only what is specific to this marketplace and never repeats
or weakens a rule of this file or of SCOPE.md.

Imports for Claude Code (other hosts read the files named above as text):

@CUSTOM.AGENTS.md
@SCOPE.md
