# Messages to the person

Applies to every failure and stop the Manager skills report, and to results. Technical detail is for the helper,
not for the message. The language rules of `operator-language.md` apply as before.

## Address

Write to the person informally. German uses "du" and the singular imperative ("Öffne", "Führe aus", "Rufe auf"),
never "Sie" or "Ihr". Other languages use their informal second person where they have one. The German examples in
this file show the register.

## Mandatory structure of every error message

```
<The action> could not be completed.
Why:
<The cause in one or two plain sentences, about the person's folder or file, named by its path.>
Solution(s):
a) <first way>
or
b) <second way>

<Then call /plugin-manager:<skill> again.>
```

- Headline, `Why:` and `Solution(s):` are always present, in this order. One way only: write `Solution:` and no
  letters. Labels in German: "Warum:" and "Lösung(en):" ("Lösung:" for one way); another language translates them.
- The headline names what the person asked for (setup, docs, modify, publish), never a helper or flow.
- `Why:` has no exit codes, JSON field names (`ok`, `checks`, `conflicts`, `changed`), script, helper or generator
  names, no words such as schema, evidence, hash, lock, transaction, manifest or migration, and no raw error text.
- `Solution(s):` gives exact commands in code and where to run them ("in your IDE, for example VS Code, or in a
  terminal"). At most two ways. The closing line names the call to repeat.
- Say what was already changed in one short closing line when something was ("The language you chose was saved.")
  and "Nothing was changed." otherwise. Never "partial changes" or field names.
- Keep it short. Details only when the person asks for them.

## Known causes

Use these wordings for the causes below (translate faithfully). Fill in the path.

| Cause | Why | Solution(s) |
| --- | --- | --- |
| The folder is no Git repository | The folder `<path>` is not recognised as a Git repository. | a) Open the folder in an IDE (for example VS Code) and initialise a Git repository there. or b) In a terminal in that folder run `git init`. |
| A plugin folder has no GitHub address | The folder `<path>` has no GitHub address yet. | Run `git remote add origin https://github.com/<owner>/<name>.git` in that folder (the repository does not have to exist yet). |
| The folder lies inside another repository | The folder `<path>` lies inside the Git repository `<root>`. | Choose the folder that is itself the repository. |
| The address is not a plain GitHub address | The address `<address>` is not a plain GitHub address. | Use the form `https://github.com/<owner>/<name>.git`, without user name or password. |
| Git is not installed | Git is not installed or cannot be found. | Install Git, then try again. |
| The marketplace folder is not a marketplace | The folder `<path>` is not a marketplace. | Choose the folder that contains the file `marketplace.json`. |
| The folder holds other content | The folder `<path>` already holds other files that are not part of a plugin. | a) Start in an empty folder. or b) Move the other files out of the folder. |
| Existing files differ | Some files in `<path>` already exist with other content. | Keep them as they are, or choose by hand which version stays (the setup asks for each file). |
| A file has an unsupported format | The file `<file>` has a format this version does not read. | Move or rename the file and call the skill again; the Manager never converts or deletes it. |

## Unknown causes

When the failure matches none of the known causes, do not guess:

- `Why:` "The cause is not known (an unexpected error)." Name what was already changed, or that nothing was.
- `Solution(s):` a) Call the same skill again; it checks the state first, so repeating is safe. or b) Run
  `/plugin-manager:verify` for a read-only check of the folder.
- When the host offers a structured question tool, ask one question: "Show technical details?" with the answers
  "Show technical details" and "No, thanks" (German: "Technische Details anzeigen" and "Nein, danke"). On yes,
  show the raw error text once in a code block under the heading "Technical details", so that it can be passed
  on; on no, end.
- Never invent a cause, never run a repair command, never retry silently.

The stop of `docs`, `modify` and `publish` at a closed gate (`flows/gate.md`) uses the same structure.
