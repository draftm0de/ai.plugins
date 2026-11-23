# Operator language acceptance (NOT RUN)

These cases require separately authorized model/host execution with fictional projects.
Runtime tests alone do not prove the agent asks or speaks in the correct language.

- Empty project, bare setup command: first question asks only preferred language;
  no default selection or domain action before the answer. Choose German: persist de,
  continue all interaction in German; English documentation/content remains English.
- New session, same project, bare command: reuse German without another question.
- Second project: ask again; do not read or alter the first project's preference.
- Explicitly change to English: persist en only in the selected project.
- German preference, message in English without a change request: keep German.
- Invalid JSON, unknown schema or symlink: stop, explain, preserve bytes and targets.
- Read-only domain action with no preference: explain the preference write accurately;
  domain action itself must remain read-only.
- Bare docs or publish command (no text, nothing set up): stops with the reason and a pointer to
  /plugin-manager:setup, in English; no question, no language saved. With German text in the call: same stop in German.
