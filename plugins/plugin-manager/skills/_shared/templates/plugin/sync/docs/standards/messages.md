# Message standards / Meldungs-Standards

Managed by the plugin manager and identical in every plugin. Do not edit it here.

## Layout

Every failure or stop message is two short paragraphs of running text separated by one blank line. No labels, no list
letters, no headings, no line break inside a sentence.

```
The <action> action could not be completed, because <cause in plain words>. <What was already changed, or that nothing was.>

Please <the way to fix it>. Then call /plugin-<name>:<skill> again.
```

- A deliberate stop says "was stopped" instead of "could not be completed".
- Two ways go in one sentence: "Please either ... or ...". At most two ways, with exact commands and where to run them
  (in an IDE such as VS Code, or in a terminal).
- The cause names the folder or file by its path. It has no exit codes, JSON field names, script, helper or generator
  names, no words such as schema, evidence, hash, lock, manifest or migration, and no raw error text.
- Say what was already changed in one sentence, or that nothing was. Never "partial changes".

## Language and address

- Write in the language of the person's text, else the saved operator language, else English. German uses "du" and the
  singular imperative ("Öffne", "Führe aus"), never "Sie" or "Ihr". Other languages use their informal form.

## One catalogue, built in code

- Layout and wording of every message live in one module of the plugin, as a catalogue keyed by a code, in each
  supported language. No other place builds the layout.
- Scripts raise failures with a code and facts (path, address); the command prints the finished message. The model
  writes that message unchanged and never composes, translates, shortens or extends it.
- A new cause is a new catalogue entry with a code, never a sentence in a skill or flow.
- A failure without a code, an error of the host or a crash gets the same layout with "the cause is not known (an
  unexpected error)", a repeat and a read-only check as ways. The raw text stays technical detail, shown only when the
  person asks.

## Evidence

Tests check that every catalogue entry has the layout in every language without technical words, that every code the
scripts raise is in the catalogue and that no other place builds the layout. Model cases check that the model writes
the finished message unchanged; they show that the text steers a model, not how often.
