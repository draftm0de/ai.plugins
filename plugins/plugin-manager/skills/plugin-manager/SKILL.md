---
name: plugin-manager
description: Central entry. Checks the state of an explicitly selected folder for this plugin and runs exactly the needed flow (operator language, configuration as plugin or marketplace, shared development skeleton, sync), re-checking after each flow. An existing managed file is replaced only by the person's explicit adopt decision, and removed only under the ownership rules for sources removed in the parent or by the person's explicit delete decision.
---

# plugin-manager (central entry)

Central entry of the Plugin Manager. Follow `../_shared/flows/entry.md` with `plugin = plugin-manager` (every helper call passes `--plugin plugin-manager`); the flows `language.md`, `skeleton.md` and `sync.md` live next to it, the plugin-specific configuration is `flows/configure.md`. Specialised actions stay in their own skills; shared rules for them are in `../_shared/WORKFLOWS.md`. Helper: `../_shared/scripts/project_setup.py`; language rules: `../_shared/references/operator-language.md`, which applies only where it does not conflict with the entry flow. Precedence: the entry's read-only rule and flow order win. In particular its direct `--set` before continuing and its rule to ask/save a missing language even for read-only actions do not apply here. Resolve paths from this loaded SKILL.md; never search host caches.

## Manager-specific rules

- Never the installed Manager or unrelated projects as target. The kinds are `plugin` (a plugin repository) and `marketplace` (a marketplace checkout); the configuration flow asks which one first.
- Configuration is two steps: the existing generator (answer with `action`, `changed`, `checks` and prose `next`, but no `ok`; success means exit 0 **and** `checks.status == "passed"`) and then `record`, which writes the configuration evidence only after that success. A configuration failure is a non-zero exit or `checks.status` other than `passed`, for example `needs_attention`: report the failing entries under `checks`, the files actually listed in `changed` and the generator's own `next` text.
- Files this entry manages in the workpackage: `.project/plugins/plugin-manager/config.json` (configuration evidence) and `.project/plugins/plugin-manager/skeleton.json` (skeleton evidence, schema_version 2); the plugin skeleton is the `common` list of `../_shared/manifests/plugin.json`, the marketplace skeleton that of `../_shared/manifests/marketplace.json`.
- Configuration uses the existing plugin-create generator with its documented prerequisites (it reads Git metadata); the entry adds no Git mutation or network action. This does not alter configure, update, verify, publish or plugin-create.
- On `ready` output only the ready line `Plugin plugin-manager Status: fully configured` (German `Plugin plugin-manager Status: vollständig konfiguriert`) and wait.
