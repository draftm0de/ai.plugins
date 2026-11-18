# Development

[Deutsch](../de/development.md) | **English**

[Home](../../README.en.md) · [Overview](README.md) · [Install](installation.md) · [Use](usage.md) · [Screens](screens.md) · [FAQ](faq.md)

## Source of truth

<!-- Root plugin.json owns identity; make sync-plugin derives committed Claude/OpenAI catalogs. Keep skills/ at root and omit manifest versions. -->

{{CONTENT_01}}

## Checks

{{CONTENT_02}}

## Packaging

<!-- Explain Makefile install-local/update-local TARGET=claude|codex, separate <plugin-name>-dev snapshots under dist/local-development, uncommitted edits, DRY_RUN=1 creating snapshots without host calls, CLI prerequisites and local-vs-account scope. Keep matching numbered/code-block formatting across hosts and languages. Explain check-plugin/sync-plugin. No plugin ZIP builder or remote install/update targets; website export is separate. Never recommend copying into host caches. -->

{{CONTENT_03}}

## CI and releases

<!-- CI validates only. Publish: reviewed diff/message, approval, commit, push, PR, checks/reviews, merge. No tag/release/catalog promotion. -->

{{CONTENT_04}}

## Maintain documentation

{{CONTENT_05}}

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.
