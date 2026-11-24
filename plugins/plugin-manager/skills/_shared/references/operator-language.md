# Operator language (binding)

## How a skill uses the language

Every skill follows these four rules and does not repeat them in its own text:

1. The language comes from `operator_language` in the output of the helper below and from nowhere else: not from the
   language of the skill text, of a file or folder name, of the command or of the person's first message. The one
   exception is a failure of the helper itself, before any language is saved: it uses the language of the person's text.
2. Everything the person reads is written in that language: previews, questions, answer labels, results and every
   finished failure message. Paths, commands and identifiers stay unchanged.
3. A script that prints text for the person receives the language: pass the operator language to `--language` or
   `--message-language`, whichever the script offers.
4. While no language is known, resolve it first (below) before anything else is shown.

Details and the helper follow.

Before any domain/setup questions or actions, resolve the operator preference in the
explicitly selected project root, never the installed plugin or a global profile.
Use the loaded skill's sibling `../_shared/scripts/operator_language.py` with
`python3 -B "<absolute helper path>" --root "<selected project root>" --skill <name of the calling skill> --message-language <language of the person's text>`.
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

The command line of the helper (options, exit codes, stored format) is described in
`operator-language-helper.md`; read it only when a call fails or you need an option.
