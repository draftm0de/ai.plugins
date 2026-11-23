# Repository architecture / Repository-Struktur

- `AGENTS.md`: common agent rules, managed by the Manager in plugin repositories; `CUSTOM.AGENTS.md`: the plugin's own instructions.
- `SCOPE.md`: confirmed goals, non-goals and acceptance criteria; draft until agreed.
- `skills/<name>/SKILL.md`: public skill entry points for plugins.
- `skills/<name>/scripts/`: distributed runtime; no imports from a developer checkout.
- `skills/setup/scripts/`: the setup state helper, entry `setup_state.py` and package `state/` (public API in `state/__init__.py`).
- `skills/_shared/`: optional shared runtime/rules, no extra SKILL.md.
- `scripts/`: development, validation and distribution helpers only.
- `tests/unit/`, `tests/integration/`, `tests/contracts/`: deterministic tests.
- `tests/behavior/`, `tests/native/`: explicit model/isolated-host tests only.
- `tests/fixtures/`, `tests/support/`: fictional data and shared helpers.
- `docs/standards/`: coding, message, test and skill standards, managed by the Manager and identical in every plugin (plugin repositories only; edited only in `skills/_shared/templates/plugin/sync/docs/standards/`).
- `docs/`: maintained documentation. Do not duplicate authoritative product facts.
- `.local/marketplace.json`: ignored machine-local associations, never committed.

Plugin repositories have plugin.json and derived host manifests, never marketplace
catalogs. Marketplace repositories have marketplace.json and derived host catalogs,
never new embedded plugins. GitHub repository creation is outside these tools.

Runtime scripts take no location or state from module globals or `__file__`. What a script reads from
the parent (manifests, templates) and the running plugin come in as an explicit context parameter
(`Context` in `skills/setup/scripts/state/context.py`). Production uses the defaults; code callers, tests
included, pass other data. Shared scripts are code, never part of the context, and the shipped command
line has no option for it. New scripts follow this; existing scripts change when they are next modified.

Root scripts are not shipped runtime. Keep runtime dependencies inside the plugin
payload. Do not store user state in the installed plugin. Use only needed directories.
Before claiming completion, compare implementation against each confirmed requirement
and distinguish missing evidence from verified contradictions. Files existing and
structural checks passing do not prove domain behavior or host acceptance.

Die Struktur ist eine Entwicklungsregel, keine Garantie für LLM-Verhalten. Das
bestätigte Zielbild bleibt maßgeblich. Fehlende Belege und tatsächliche Widersprüche
getrennt berichten; fachliche Erfüllung braucht Source-Review und passende Tests.
