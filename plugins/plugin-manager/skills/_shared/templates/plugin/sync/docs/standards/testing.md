# Test standards / Test-Standards

Managed by the plugin manager and identical in every plugin. Do not edit it here.

## Structure

Tests are ordered by type first, then by skill or component. Python names use underscores. Create only the
directories that are needed, and add `__init__.py` to every discovered directory.

| Directory | Purpose |
| --- | --- |
| `tests/unit/` | single functions, no host, no model |
| `tests/integration/` | tools, files and temporary repositories together |
| `tests/contracts/` | skill, manifest, catalogue and package contracts |
| `tests/behavior/` | explicitly started model tests |
| `tests/native/` | real host CLIs with isolated profiles |
| `tests/fixtures/` | fictional data |
| `tests/support/` | shared helpers without tests of their own |

`make test` runs unit, integration and contracts only, never native or model tests. A missing layer reports
`NOT RUN`, which is not a passed test. Regressions belong to their test type, not to a `regression` directory.

## Rules

- Every confirmed requirement in `SCOPE.md` has an acceptance test named in its `Test:` line. Generated structural
  tests and tests of instruction text do not establish product behavior.
- Rule tests run the real scripts unchanged. Data the code reads from its parent comes in as the context (see
  `coding.md`) with fixed, fictional bytes defined in the test. Expectations come from literals, never from production
  templates.
- Delivery tests copy the real parent data and check only what is stable. Fail writes and file operations selectively;
  everything else runs for real in temporary directories.
- Fixtures are fictional. Never use private data, credentials or a personal installation.
- Native tests use isolated homes and never change a personal installation.

## Model tests

- The runner is the managed `tests/behavior/run_cases.py` (`make test-behavior CLI=claude|codex`); the cases are the plugin's own
  `tests/fixtures/skills/cases.json`. Without cases it reports `NOT RUN`.
- A case holds the real skill texts, the output of the commands the skill starts with, the conversation so far and a
  deterministic expectation (language, required and forbidden text, forbidden commands, next step). The model has no
  tools; grading is deterministic.
- Add a case for every rule a model must follow, and a unit test for the grading of each case.
- Report what the run shows: one run on one model shows that the text steers a model, not how often. A host run
  stays separate.

## Reporting

Run tests only as a separately authorized step and report the actual result. Local success does not certify a
published or host acceptance.
