# Flow: operator language

Used when `status` says `next: language`. No plugin.json, Git or origin is needed.

1. Ask alone which operator language the person prefers (host question tool if available, otherwise one short chat question) and wait for an actual answer. A language the person already named explicitly for this project counts. A preselected option, silence, or anything inferred from files, names or these instructions does not.
2. Save it: `python3 -B "<helper>" language --target "<folder>" --plugin <plugin> --language <tag>`. The helper checks all conflicts first, ensures the exact rule `/.project/operator.json` in `.gitignore`, then stores the language through `operator_language.py`.
3. Check `ok` and the exit code. On `ok: false` or exit 1 report the failed language step in the plain words of `../../_shared/references/messages.md` (what is wrong, what was already saved, what to do) and stop.
4. On success run `status` again (see `entry.md`). Use the language from now on.
