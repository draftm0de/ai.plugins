# Scope/source model review evaluations

The separate [`create --kind plugin` acceptance cases](plugin_create_acceptance.md) specify
manual checks for licensing questions and conversation language. They are not run by
the review harness below and have not been executed merely by adding the specification.

Run explicitly from the Manager checkout (model calls may consume credits):

```sh
make test-behavior CLI=claude
make test-behavior CLI=codex
make test-behavior CLI=claude CASE=correct_consent
python3 -B tests/behavior/run_review.py --list
```

The versioned fictional cases live in `tests/fixtures/review/cases.json`. Each model
receives the same review instructions, the trusted static helper's observed output,
and the complete fixture files with line numbers. Expected outcomes are withheld.
No candidate data, real project source or credentials are included in prompts.
Authentication is performed by the installed CLI; no credentials are copied or logged.

Claude runs with safe/restricted mode and no tools or persistent session. Codex ignores
user configuration, disables plugin/hooks/app/shell/browser/agent features, uses a
read-only sandbox and an ephemeral session. The working directory is temporary;
fixture bytes are compared before/after. These are prompt-only semantic evaluations,
not native installation or unrestricted tool-use acceptance. The harness itself
materializes fixtures and runs the trusted static verifier; it never runs fixture code.

Cases cover correct consent logic, correct relative imports, writing before consent,
vacuous tests, missing source and an injected unsupported success instruction.
Grading checks requirement verdicts, required findings, false alarms, source citations,
unsupported test/runtime/publication claims and unchanged fixtures. Narrative checks
are heuristics, so every model report also requires human semantic review. Absence of
execution evidence is not a source defect. Source correctness and test coverage are
separate dimensions. Passing examples do not prove general LLM reliability.

Each run creates a new ignored `.tmp/tests/behavior/review/<cli>/<timestamp>/` directory.
`BEHAVIOR_OUTPUT=...` chooses a new output directory; existing directories are refused.
Prompts, raw CLI output, diagnostics, structured reports, CLI version and summaries
are retained separately. Failed runs are preserved; retries never replace them.
No model calls are part of `make test`. Missing CLI/auth/network is a failed run, not a
passed test. No tools are installed automatically and no plugin installation is changed.

## Skill behavior (setup, docs, modify, publish)

`make test-behavior-skills CLI=claude` (or `codex`, optionally `CASE=<id>`, `python3 -B tests/behavior/run_skills.py --list`)
gives the model the real skill texts, the output of the helper commands the skill starts with (fictional, already run) and the
conversation so far. It has no tools and answers with the reply and the commands it would run. The grading is deterministic:
language of the stop message (English for a bare command, the person's language otherwise), the pointer to
`/plugin-manager:setup`, no questions where none belong, no forbidden command (for example `modify.py` without `--dry-run`
before a yes). The cases are in `tests/fixtures/skills/cases.json`; the deterministic unit tests of the cases and the grading
are `tests/unit/behavior/test_skill_cases.py`.

This evaluates the instruction texts with a model. It does not test host routing (`/plugin-manager:<skill>` reaching the
skill); that needs a host, see `make test-native` and `make install-local`. Model calls may consume credits and answers vary.
