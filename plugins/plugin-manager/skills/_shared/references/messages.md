# Messages to the person

Applies to every failure and stop the Manager skills report, and to results. Technical detail is for the helper,
not for the message. The language rules of `operator-language.md` apply as before.

## Address

Write to the person informally. German uses "du" and the singular imperative ("Öffne", "Führe aus", "Rufe auf"),
never "Sie" or "Ihr". Other languages use their informal second person where they have one. The German examples in
this file show the register.

## Mandatory structure of every error message

Two short paragraphs of running text, separated by one blank line. No labels, no list letters, no line break inside
a sentence.

```
The <action> action could not be completed, because <the cause in plain words>. <What was already changed, or nothing.>

Please <the way to fix it>. Then call /plugin-manager:<skill> again.
```

Two ways in one sentence: "Please either <first way> or <second way>." Example (English):

```
The setup action could not be completed, because the folder /Users/demo/plugin.a is not recognised as a Git repository. The language you chose was saved.

Please either initialise a Git repository in an IDE (for example VS Code) or run `git init` in a terminal in that folder. Then call /plugin-manager:setup again.
```

- The first paragraph names what the person asked for (setup, docs, modify, publish), never a helper or flow, says
  "could not be completed" (a deliberate stop: "was stopped"), then `because` and the cause. The cause names the
  folder or file by its path and has no exit codes, JSON field names (`ok`, `checks`, `conflicts`, `changed`),
  script, helper or generator names, no words such as schema, evidence, hash, lock, transaction, manifest or
  migration, and no raw error text.
- Say what was already changed in one short closing sentence of the first paragraph when something was ("The
  language you chose was saved.") and "Nothing was changed." otherwise. Never "partial changes" or field names.
- The second paragraph starts with the request ("Please ..."; German: the singular imperative, "Führe ... aus.")
  and gives exact commands in code and where to run them ("in your IDE, for example VS Code, or in a terminal"). At
  most two ways. It ends with the call to repeat, unless that is the request itself.
- Keep it short. Details only when the person asks for them.
- Never write the answer as a bullet list, a recap or a heading structure; the shape above is the whole message. Write
  it as your reply to the person, in full, never only in a status, summary or wrap-up field of the host.

## The wording is not yours

The wording of every known cause, in both languages, lives in one place: the catalogue of
`../../setup/scripts/state/messages.py` (R26). Scripts raise a failure with a code; the command prints the finished
message. You write that message unchanged, you never compose, translate, shorten or extend it.

- A helper answer (setup state helper) carries the finished text in `message`.
- A command line (`workflows.py`, `modify.py`) prints it on stderr. The line `[Technical details, only when the
  person asks: ...]` after it is not part of the message; show it only when the person asks.
- Pass `--message-language <language of the person's text>` where the command accepts it; without the option the
  saved operator language counts, else English. Pass `--changed language` when the language was saved before the
  call.
- Known causes today: `git_missing`, `not_a_repository`, `plugin_without_repository`, `no_origin`,
  `inside_repository`, `address_not_plain`, `address_differs`, `other_content`, `existing_differs`,
  `unsupported_format`, `not_configured`, `invalid_name`, `empty_display_name`, `empty_description`,
  `nothing_to_change`, and the closed gate. A new cause is a new entry in the catalogue, never a sentence in a flow.

## Unknown causes

A failure without a catalogue code gets the "cause not known" message from the same module; do not guess:

- When a command ends without a finished message (an error of the host, a crash), run
  `python3 -B "../../setup/scripts/setup_state.py" explain --action <skill> --message-language <language> --error "<raw text>"`
  and write the `message` it prints unchanged. It says the cause is not known and offers `verify` and a repeat.
- When the host offers a structured question tool, ask one question: "Show technical details?" with the answers
  "Show technical details" and "No, thanks" (German: "Technische Details anzeigen" and "Nein, danke"). On yes,
  show the raw error text once in a code block under the heading "Technical details"; on no, end.
- Never invent a cause, never run a repair command, never retry silently.

The stop of `docs`, `modify` and `publish` at a closed gate (`flows/gate.md`) is produced the same way (`gate_message`).
