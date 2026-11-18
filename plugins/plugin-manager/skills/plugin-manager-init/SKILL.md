---
name: plugin-manager-init
description: Inspect the source skill, clarify unresolved facts, then initialize a separate empty plugin repository. Never overwrite or move existing sources.
---

# Manager init

Inspect the source skill, clarify unresolved facts, then initialize a separate empty plugin repository. Never overwrite or move existing sources.

Read `../plugin-manager/SKILL.md` and follow its **init** action. This is a thin plugin entry point; all rules and templates live in that canonical skill. Ask for paths only if they cannot be determined.

Resolve the plugin name before initialization: reuse a name already explicitly confirmed by the user, otherwise ask. Pass `--plugin-name`; repository marketplace names equal that plugin name and local development appends `-dev`.
