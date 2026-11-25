<!--
This file comes from the plugin manager and is managed by it: every marketplace has the same task. Do not edit it
here. Which plugins this marketplace lists is stated in marketplace.json; own instructions belong in CUSTOM.AGENTS.md.
-->

# Marketplace scope

Status: confirmed

## Purpose

A marketplace is the catalog from which a person adds one source in Claude or Codex and installs the plugins listed
in `marketplace.json`. Name, owner and listed plugins are what distinguishes one marketplace from another.

## Non-goals

A marketplace contains no plugin and no skill, installs and publishes nothing by itself and says nothing about
whether a listed plugin works: every plugin lives in its own repository with its own scope and tests.

## R1: Catalog only

Status: confirmed
Acceptance: `marketplace.json` is the only catalog edited by hand. An entry has exactly `name` (unique lowercase kebab-case, equal to the plugin's own name), `displayName`, `description` and `repository` (GitHub HTTPS clone URL ending in `.git`, without credentials); no local `path`, and no `version` for an entry or the marketplace.
Source: scripts/marketplace.py
Test: tests/contracts/test_marketplace_catalogs.py

## R2: Generated host catalogs

Status: confirmed
Acceptance: `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` are generated with `python3 -B scripts/marketplace.py sync`, checked with `python3 -B scripts/marketplace.py check` and never edited by hand.
Source: scripts/marketplace.py
Test: tests/contracts/test_marketplace_catalogs.py

## R3: Local development

Status: confirmed
Acceptance: `make install-local` installs the local checkouts as a separate development marketplace and publishes nothing. Their paths live only in the ignored `.local/marketplace.json`; `local-marketplace.example.json` is an example and is never read.
Source: scripts/local_plugins.py
Source: scripts/plugin_payload.py
Test: tests/contracts/test_local_plugins.py
Test: tests/contracts/test_plugin_payload.py

## R4: Current formats only

Status: confirmed
Acceptance: Only the current formats are supported. Anything else is rejected with its reason before a write; nothing is converted or deleted. Own tests lie under `tests/<layer>/`, use fictional data and never depend on which plugins are listed.
Source: scripts/marketplace.py
Source: scripts/run_tests.py
Test: tests/contracts/test_marketplace_catalogs.py
Test: tests/contracts/test_run_tests.py
