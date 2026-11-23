---
name: docs
description: Re-read canonical sources and refresh documentation in the repository-selected languages. Reuse the source and language configuration manifest without duplicating product facts.
---

# Manager docs

Re-read canonical sources and refresh documentation in the repository-selected languages. Reuse the source and language configuration manifest without duplicating product facts.

Read `../_shared/WORKFLOWS.md` and follow its **docs** action. This is a thin plugin entry point; all rules and templates live in that shared workflow reference. Ask for paths only if they cannot be determined.

Messages to the person (failures, stops, results) follow `../_shared/references/messages.md`: outcome first, the cause in plain words, one concrete next step, no technical terms.

## State gate

Before reading sources or writing documentation follow `../_shared/flows/gate.md` (`setup_state.py gate --action docs`). When the gate is closed, stop as that flow says: the structured message (headline, Why, Solution), then the question whether to run `/plugin-manager:setup`; this skill writes nothing then. Only `setup` changes configuration, skeleton files or sync decisions.
