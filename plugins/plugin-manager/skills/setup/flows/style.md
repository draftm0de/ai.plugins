# Flow: writing style of the documentation

Used when `status` says `next: style`: `docs/style.md` is missing. It describes how the documentation of this repository is written; the repository owns it and the Manager never changes it.

1. Ask once (host question tool if available), in the operator language, with exactly two answers: "Use the Manager's template" or "Describe my own style". Add one short example for the second: "Address readers as du, short sentences, no marketing words, explain technical terms once."
2. Template: run `python3 -B "<helper>" style --target "<folder>" --plugin <plugin> --from-template`.
3. Own style: ask for the style in the person's words, show the complete file text, and only after an explicit yes run `python3 -B "<helper>" style --target "<folder>" --plugin <plugin> --text "<confirmed text>"`.
4. No answer is no decision: end without writing. Never add a "skip" answer.
5. On `ok: false` or exit 1 write the `message` of the answer unchanged (`../../_shared/references/messages.md`) and stop. On success report the created file by its path only, say that the person should read and adjust it, and run `status` again.
