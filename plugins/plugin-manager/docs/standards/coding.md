# Coding standards / Coding-Standards

Managed by the plugin manager and identical in every plugin. Do not edit it here; a deviation is a finding of
`verify`. The plugin's own goal and requirements live in `SCOPE.md`, never here.

## Layout

- Runtime code lives under `skills/<skill>/` (scripts in `skills/<skill>/scripts/`); code shared by several skills
  lives under `skills/_shared/` without a `SKILL.md`. Root `scripts/` holds development tooling only and is never
  shipped. Runtime code imports nothing from a developer checkout.
- Python 3.10+, standard library only unless `SCOPE.md` confirms a dependency. Run scripts with `python3 -B`.
- A module name must not collide with a likely local variable (`target`, `plan`, `lock`, `language`).

## Context instead of globals

- A runtime script takes no location or state from module globals or `__file__`. What it reads from its parent
  (manifests, templates) and the name of the running plugin come in as one explicit context parameter.
- Production uses the default context. Code callers, tests included, pass other data. The shipped command line has no
  option for the context.
- The one allowed use of `__file__` is the entry file locating its own scripts folder to import from.
- Shared scripts are code, never part of the context.

## Data and formats

- Only the current format is read. No legacy layouts, compatibility aliases, fallback discovery or automatic
  migration. An unsupported file is rejected with a concrete reason before any write; user data is never deleted or
  overwritten.
- A command that only reads writes nothing. A command that writes checks the whole change first, preserves foreign
  files and rolls back when a write fails.
- User state never lives in the installed plugin. Never read private workspaces, credentials or ignored personal data.

## Failures

- A failure a person can reach carries a catalogue code and the facts of its wording (see `messages.md`). Never raise a
  free text for a person; a failure without a code is reported as "cause not known".
- Never run a repair command, retry silently or guess a cause.
