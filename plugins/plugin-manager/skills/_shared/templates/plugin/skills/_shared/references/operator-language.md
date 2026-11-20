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
