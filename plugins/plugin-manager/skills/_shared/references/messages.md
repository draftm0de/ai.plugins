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
<The action> could not be completed, because <the cause in plain words>. <What was already changed, or nothing.>

Please <the way to fix it>. Then call /plugin-manager:<skill> again.
```

Two ways in one sentence: "Please either <first way> or <second way>." Example (English):

```
The setup could not be completed, because the folder /Users/demo/plugin.a is not recognised as a Git repository. The language you chose was saved.

Please run `git init` in that folder, in your IDE (for example VS Code) or in a terminal. Then call /plugin-manager:setup again.
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

## Known causes

Use these wordings for the causes below (translate faithfully). Fill in the path. The cause continues the sentence
after "because"; the way continues "Please ...".

| Cause (after "because") | Way |
| --- | --- |
| the folder `<path>` is not recognised as a Git repository | either initialise a Git repository in an IDE (for example VS Code) or run `git init` in a terminal in that folder |
| the folder `<path>` has no GitHub address yet | run `git remote add origin https://github.com/<owner>/<name>.git` in that folder (the repository does not have to exist yet) |
| the folder `<path>` lies inside the Git repository `<root>` | choose the folder that is itself the repository |
| the address `<address>` is not a plain GitHub address | use the form `https://github.com/<owner>/<name>.git`, without user name or password |
| Git is not installed or cannot be found | install Git |
| the folder `<path>` is not a marketplace | choose the folder that contains the file `marketplace.json` |
| the folder `<path>` already holds other files that are not part of a plugin | either start in an empty folder or move the other files out of the folder |
| some files in `<path>` already exist with other content | keep them as they are, or choose by hand which version stays (the setup asks for each file) |
| the file `<file>` has a format this version does not read | move or rename the file (the Manager never converts or deletes it) |

## Unknown causes

When the failure matches none of the known causes, do not guess:

- First paragraph: "... could not be completed, because the cause is not known (an unexpected error)." Name what was
  already changed, or that nothing was.
- Second paragraph: "Please either call the same skill again (it checks the state first, so repeating is safe) or
  run `/plugin-manager:verify` for a read-only check of the folder."
- When the host offers a structured question tool, ask one question: "Show technical details?" with the answers
  "Show technical details" and "No, thanks" (German: "Technische Details anzeigen" and "Nein, danke"). On yes,
  show the raw error text once in a code block under the heading "Technical details", so that it can be passed
  on; on no, end.
- Never invent a cause, never run a repair command, never retry silently.

The stop of `docs`, `modify` and `publish` at a closed gate (`flows/gate.md`) uses the same structure, in one sentence: "The <action> action was stopped, because this folder is not set up yet, or only partly (<reason>)." and "Please run /plugin-manager:setup first."
