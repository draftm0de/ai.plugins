# Gate: state check before a writing skill

Used by `docs`, `modify` and `publish` before they prepare or write anything. Only `setup` brings a repository into the configured state; the gate never does.

1. Determine the explicitly selected folder (user input or current project). Never the installed plugin directory.
2. Run `python3 -B "../../setup/scripts/setup_state.py" gate --target "<folder>" --plugin plugin-manager --action <docs|modify|publish>` (JSON, writes nothing, needs no Git, origin or marketplace).
3. `ready: true` (exit 0): continue with the skill.
4. `ready: false` (exit 1): stop and write `message` from the answer unchanged, nothing else. It follows the mandatory structure of `../references/messages.md` (two paragraphs of running text): "The <action> action was stopped, because this folder is not set up yet, or only partly (<reason>)." then a blank line and "Please run /plugin-manager:setup first." Write it in the language of the person's text in this call, the German form is "Die Aktion <action> wurde abgebrochen, weil dieser Ordner noch nicht oder nur teilweise eingerichtet ist (<Grund>)." then a blank line and "Führe zuerst /plugin-manager:setup aus."; another language gets a faithful translation, and `/plugin-manager:setup` and the action name stay as they are. With a bare command and no text, write it in English. `detail` (technical, may be empty) is shown only when the person asks. Store nothing, never guess a language from files or paths (the operator language belongs to `setup`), do not run any setup, sync or configuration flow yourself and do not retry. The skill writes nothing and prepares nothing.
5. Then, when the host offers a structured question tool, ask exactly one question with exactly two answers (English: "Run /plugin-manager:setup now?" with "Yes, run it" and "No, stop"; German: "Soll ich /plugin-manager:setup jetzt ausführen?" with "Ja, ausführen" and "Nein, abbrechen"; another language translates them). Without such a tool ask nothing: the two lines are the whole answer.
   - Yes: hand over to the skill `setup` (`/plugin-manager:setup`) and end. Its dialogue runs the open flow; the original action does not continue by itself, the person calls it again afterwards. The gated skill still writes nothing.
   - No, a dismissed or unanswered question: end without any further step and do not ask again in this call.

`next` is one of `stop` (technical conflict), `language`, `configure`, `skeleton`, `sync`; `ready` is never an open state. An accepted deviation of a managed file does not close the gate (`ready` stays true). The gate is not product acceptance.

`verify` does not use the gate: it continues and reports a pending setup or sync as a finding.
