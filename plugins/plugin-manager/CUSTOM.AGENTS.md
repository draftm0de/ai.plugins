<!--
Instructions that are specific to this plugin. AGENTS.md (managed by the plugin manager) and docs/standards/
always apply first; never repeat or weaken them here. Keep this file short.
-->

# Plugin-specific instructions

- After changing any file under `skills/_shared/templates/*/sync/`, run `make build-skeleton-hashes` and commit the
  rewritten `skills/_shared/manifests/*.sync.json`. Never edit those files by hand. CI runs `make check-skeleton-hashes`.
- Some files exist as identical copies, which tests enforce: `verify.py` (skill, `scripts/`, both sync templates and the
  repository root), the standards and `AGENTS.md` (templates and this plugin), `messages_base.py` and
  `operator_language.py` (templates and `skills/_shared/scripts/`). Change the original and copy it.
