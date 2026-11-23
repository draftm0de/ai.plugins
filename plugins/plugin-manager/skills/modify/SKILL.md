---
name: modify
description: Change what a plugin or marketplace repository states about itself - technical name, display name and description (a marketplace has no description). Shows the consequences first and writes only after the person's explicit yes. Does not rewrite documentation, tests or the repository URL; the marketplace association stays in setup.
---

# Manager modify

Read `../_shared/WORKFLOWS.md` and follow its **modify** action. This is a thin plugin entry point; the rules live in that shared workflow reference. The helper is `scripts/modify.py`; it takes the kind from the configuration evidence of the workpackage, never from the call.

Messages to the person (failures, stops, results) follow `../_shared/references/messages.md`: two short paragraphs of running text (what could not be done, because of what, what was changed; then the request with the exact way and the call to repeat), no labels, no technical terms.

## State gate

Before asking anything follow `../_shared/flows/gate.md` (`setup_state.py gate --action modify`). When the gate is closed, stop as that flow says: the one-sentence stop message, then the question whether to run `/plugin-manager:setup`; this skill writes nothing then. Only `setup` changes configuration, skeleton files or sync decisions.

## Dialogue

1. Ask what to change: name, display name, description (marketplace: name and display name only). Take values the person gave in the call; never invent them. One targeted question at a time; a cancelled or unanswered question is a pause.
2. Show the consequences with `python3 -B "scripts/modify.py" --root "<folder>" [--name N] [--display-name D] [--description T] --dry-run` (writes nothing): the files that would change, whether the marketplace entry follows, and for a marketplace the affected plugins. Name only paths and facts, no file contents.
3. Write only after the person's explicit yes to exactly these values: run the same call without `--dry-run`. Success is exit 0; a refusal prints `ERROR:` and changed nothing.
4. Report `changed`, `catalog_entry_remains` and the `follow_up` notes: call forms and documentation are refreshed with `/plugin-manager:docs`, the changed files are published through `/plugin-manager:publish`. Never commit, push, install or publish.
