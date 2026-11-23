# Gate: state check before a writing skill

Used by `docs` and `publish` before they prepare or write anything. Only `setup` brings a repository into the configured state; the gate never does.

1. Determine the explicitly selected folder (user input or current project). Never the installed plugin directory.
2. Run `python3 -B "../../setup/scripts/setup_state.py" gate --target "<folder>" --plugin plugin-manager` (JSON, writes nothing, needs no Git, origin or marketplace).
3. `ready: true` (exit 0): continue with the skill.
4. `ready: false` (exit 1): stop. Name `next` and `reason` and point to `/plugin-manager:setup`, which runs the open flow. Write this one message in the language of the person's text in this call; with a bare command and no text, write it in English. Store nothing, ask nothing and never guess a language from files or paths (the operator language belongs to `setup`). Do not run any setup, sync or configuration flow yourself and do not ask the questions of those flows. The skill writes nothing, prepares nothing and does not retry.

`next` is one of `stop` (technical conflict), `language`, `configure`, `skeleton`, `sync`; `ready` is never an open state. An accepted deviation of a managed file does not close the gate (`ready` stays true). The gate is not product acceptance.

`verify` does not use the gate: it continues and reports a pending setup or sync as a finding.
