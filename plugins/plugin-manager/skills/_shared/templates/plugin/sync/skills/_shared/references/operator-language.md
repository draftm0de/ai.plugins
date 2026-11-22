# Operator language (binding)

Before any domain/setup questions or actions, resolve the operator preference in the
explicitly selected project root, never the installed plugin or a global profile.
Use the loaded skill's sibling `../_shared/scripts/operator_language.py` with
`python3 -B "<absolute helper path>" --root "<selected project root>"`.
Resolve paths from the actually loaded SKILL.md; never search host caches. If the
project is ambiguous, ask only which project to use first.

A missing preference returns `needs_choice: true` without writing. Ask only which
language the operator prefers and wait for an actual answer. Use the host's question
tool if available (Deutsch / English plus free text for another language); otherwise
ask briefly in chat. Conversation language can localize this first question, but
must not silently become the saved preference. An explicit preference already given
in this session counts as the answer; a preselected option or silence does not.
Save that answer with `--set <language-tag>` (e.g. de, en, pt-BR) before continuing.
Never guess a language from technical names, documentation, website content or the
language of the skill instructions. Do not continue if saving fails.

The helper persists only `{"schema_version": 1, "operator_language": "de"}` in
`.project/operator.json` of the selected project. It is not a website manifest or
documentation policy. Do not inspect unrelated private state. Unsupported or corrupt
preferences and symlinks fail explicitly without overwriting or migrating data.

On later calls, including bare slash commands and new conversations, reuse the saved
language without asking again. All questions, choices, progress and final answers use
it; technical identifiers stay unchanged. Explicit requests to change the operator
language update this preference; merely writing a message in another language does
not. Preferences in other projects are unaffected. Website/content/documentation
languages remain independent and must not be changed by this step.

For read-only actions, reading an existing preference remains read-only. If missing,
ask and save only this communication preference before the read-only domain action;
never describe the entire invocation as write-free. This gate adds no permission for
installation, publication or domain operations.

## Language of all visible text

Once the operator language is known, every visible text you write yourself uses it, not only the main answer: reports, questions and choice labels, and, where the host lets you fill them, the fields of a closing summary or next-step card (summary, the question, button labels) and any follow-up offer. Apply the language before output; do not leave such text in English because the skill instructions, helper output or JSON are English. Technical identifiers, paths, commands and JSON keys are not translated. Fixed labels the host itself supplies cannot be guaranteed, and no card is forced when it is unnecessary.

## Technical reference of the helper

The canonical source is this generator template; the Plugin Manager and every newly
generated plugin ship their own byte-identical copy. The helper needs Python 3.10+ and
the standard library only; it runs from any copy without a Manager checkout, Git
repository or `PYTHONPATH`, and starts no external program or network access.

CLI: `operator_language.py --root <project> [--set <language-tag>]`.

- Without `--set` it only reads. Missing file: exit 0 with
  `{"operator_language": null, "needs_choice": true}`; nothing is created.
- Valid file: exit 0 with `{"operator_language": "<tag>", "needs_choice": false}`.
- `--set <tag>` validates the tag (`[a-z]{2,3}` with optional `-` subtags, e.g. `de`,
  `pt-BR`), checks the existing state, then writes atomically (temporary file and
  replace) and prints the same result shape. An identical stored value is not rewritten.
- Exit codes: 0 = successful operation, including a missing preference; 1 = validation,
  format, path or I/O error within the operation; 2 = invalid CLI invocation (for
  example missing `--root` or unknown arguments), as reported by `argparse`.
- Every operation error with exit 1 (invalid tag, corrupt JSON, unsupported `schema_version`, wrong types,
  extra keys, symlink in the managed path, file/directory conflict (including a regular
  file named `.project`, also when reading), missing project,
  read or write failure) writes a message to stderr and nothing to stdout. Such states
  are never reported as missing and existing data is never overwritten.

The caller is responsible for the explicit user choice and the dialogue; the helper
cannot verify consent for a passed string. It manages only `.project/operator.json`
and, when saving, the parent `.project/`. It never edits `.gitignore`; ignoring the file
is a project-setup concern (newly generated plugin repositories ignore
`/.project/operator.json`). Pass the project root with resolved (symlink-free) parents.
Atomic replacement does not protect against arbitrary concurrent foreign writers.
