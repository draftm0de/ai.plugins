---
name: verify
description: Detect plugin or marketplace structure and report production-readiness gaps. Distinguish automated structural checks from unverified host acceptance.
---

# Manager verify

Detect plugin or marketplace structure and report production-readiness gaps. Distinguish automated structural checks from unverified host acceptance.

Read `../_shared/WORKFLOWS.md` and follow its **verify** action. This is a thin plugin entry point; all rules and templates live in that shared workflow reference. Ask for paths only if they cannot be determined.

Use `../_shared/scripts/verify.py --source TARGET --kind auto` for context-aware verification. TARGET comes from the user or current project root, never from this plugin installation. Reject ambiguous roots. Use --kind plugin or --kind marketplace when the expected type is explicit. This action is read-only; configuration and repair belong to a separate action.

Report `structure_valid` independently from `local_development.complete`. Missing local checkout mappings on a fresh clone mean local checks are unavailable; they do not invalidate the published structure. Installation requires those checkouts, but verification never installs them.

## Explicit scope/source review

When asked to compare target requirements with implementation, read
`../_shared/references/scope-review.md` in full. Use the shared helper with `--review`,
then perform the actual requirement-by-requirement source/test comparison as instructed.
`SCOPE.md` is authoritative only for confirmed requirements; never infer the target
from code or silently promote draft requirements. Cite concrete source lines, explain
why a change is needed, distinguish contradictions from missing evidence, and report
unexecuted tests. The helper's `ready_for_source_review` is not semantic acceptance.
No repairs, code execution or tests during verify. Keep exactly the same read-only boundary.
