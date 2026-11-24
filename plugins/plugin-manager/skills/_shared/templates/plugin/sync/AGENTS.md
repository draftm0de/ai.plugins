<!--
This file comes from the plugin manager and is managed by it: do not edit it here, changes are overwritten or reported.
Write your plugin's own instructions in CUSTOM.AGENTS.md.
-->

# Development rules

Read SCOPE.md and docs/architecture.md before implementation. Clarify missing or
contradictory requirements; never infer product requirements from existing code.
Keep confirmed scope separate from implementation evidence. Preserve unrelated edits.

Implement plugin runtime under skills/<skill>/; shared runtime may live under
skills/_shared/ without a SKILL.md. Root scripts/ contains development tooling only.
Marketplace repositories own catalogs; plugin repositories never own catalogs.
Follow the layered tests described in tests/README.md. Add acceptance tests for
confirmed requirements. Generated structural tests do not establish product behavior.

Use verify for read-only checks and its explicit --review mode for scope/source
review. Do not execute target code as part of review. Run tests only as a separately
authorized development step and report actual results. Do not change scope to hide
implementation gaps. Never read private workspaces, credentials or ignored personal data.
Do not install tools, commit, push or publish without the corresponding authorization.

## Current formats only

No legacy layouts, compatibility aliases, fallback discovery or automatic migrations.
Reject unsupported formats explicitly before writes; preserve all existing user data.
Changes to rules may make an existing plugin fail verification. Update it only under
an explicit implementation request; never weaken scope to accept outdated content.

## Operator language

Every public skill must load `skills/_shared/references/operator-language.md` before
setup/domain interaction. Preserve this gate when replacing the skeleton or adding
skills. Persist the explicit preference per consuming project; never in the plugin.

## Standards

Before implementing, read `docs/standards/coding.md`, `messages.md`, `testing.md` and `skills.md`. They are
managed by the plugin manager and identical in every plugin: never edit them here, never copy their text into
SCOPE.md and never deviate from them. SCOPE.md holds only the goal and requirements of this plugin; when it
contradicts a standard, the standard wins and `verify` reports the contradiction.

## Plugin-specific instructions

Also read `CUSTOM.AGENTS.md` when it exists. It holds only what is specific to this plugin and never repeats or
weakens a rule of this file or of the standards.

Imports for Claude Code (other hosts read the files named above as text):

@CUSTOM.AGENTS.md
@docs/standards/coding.md
@docs/standards/messages.md
@docs/standards/testing.md
@docs/standards/skills.md
