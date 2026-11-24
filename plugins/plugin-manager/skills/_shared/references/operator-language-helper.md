# Operator language: technical reference of the helper

The canonical source is this generator template; the Plugin Manager and every newly
generated plugin ship their own byte-identical copy. The helper needs Python 3.10+ and
the standard library only (plus its managed sibling `messages_base.py`, imported only to print a failure message); it runs from any copy without a Manager checkout, Git
repository or `PYTHONPATH`, and starts no external program or network access.

CLI: `operator_language.py --root <project> [--set <language-tag>] [--skill <skill>] [--message-language <de|en>]`. `--skill` and `--message-language` only shape a failure message.

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
  read or write failure) writes the finished failure message (layout and wording of `messages_base.py`; a failure without a code is reported as not known) to stderr and nothing to stdout. Write it to the person unchanged. Such states
  are never reported as missing and existing data is never overwritten.

The caller is responsible for the explicit user choice and the dialogue; the helper
cannot verify consent for a passed string. It manages only `.project/operator.json`
and, when saving, the parent `.project/`. It never edits `.gitignore`; ignoring the file
is a project-setup concern (newly generated plugin repositories ignore
`/.project/operator.json`). Pass the project root with resolved (symlink-free) parents.
Atomic replacement does not protect against arbitrary concurrent foreign writers.
