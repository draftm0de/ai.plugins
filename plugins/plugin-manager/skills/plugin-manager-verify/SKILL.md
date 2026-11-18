---
name: plugin-manager-verify
description: Audit the plugin structure and report production-readiness gaps. Distinguish automated structural checks from unverified host acceptance.
---

# Manager verify

Audit the plugin structure and report production-readiness gaps. Distinguish automated structural checks from unverified host acceptance.

Read `../plugin-manager/SKILL.md` and follow its **verify** action. This is a thin plugin entry point; all rules and templates live in that canonical skill. Ask for paths only if they cannot be determined.

Use `../plugin-manager/scripts/verify.py --source TARGET --kind auto` for context-aware verification. TARGET comes from the user or current project root, never from this plugin installation. Reject ambiguous roots. Prefer explicit plugin-verify or marketplace-verify when the type is known. This action is read-only; configuration and repair belong to a separate action.
