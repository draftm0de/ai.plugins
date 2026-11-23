---
name: docs
description: Re-read canonical sources and refresh documentation in the repository-selected languages. Reuse the source and language configuration manifest without duplicating product facts.
---

# Manager docs

Re-read canonical sources and refresh documentation in the repository-selected languages. Reuse the source and language configuration manifest without duplicating product facts.

Read `../_shared/WORKFLOWS.md` and follow its **docs** action. This is a thin plugin entry point; all rules and templates live in that shared workflow reference. Ask for paths only if they cannot be determined.

## State gate

Before reading sources or writing documentation follow `../_shared/flows/gate.md` (`setup_state.py gate`). When the gate is closed, stop with the reason and a pointer to `/plugin-manager:setup`; this skill writes nothing then. Only `setup` changes configuration, skeleton files or sync decisions.
