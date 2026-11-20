# Product scope / Produktzielbild

Status: draft

No domain requirements have been confirmed. This document is the desired behavior,
not a summary derived from the implementation. / Fachliche Anforderungen sind noch
nicht bestätigt. Dieses Dokument beschreibt das Soll, keine Zusammenfassung des Codes.

## Purpose / Zweck

Pending confirmation / Noch zu bestätigen.

## Non-goals / Nicht-Ziele

Pending confirmation / Noch zu bestätigen.

## Requirements / Anforderungen

Add confirmed requirements as level-two headings `## R1: Short title` (R2, R3, ...).
Each requirement uses these fields; keep unconfirmed requirements marked draft:

- `Status: confirmed` or `Status: draft`
- `Acceptance: Observable acceptance criterion in the chosen project language`
- `Source: skills/example/scripts/runtime.py` (one repository-relative file per line)
- `Test: tests/integration/example/test_runtime.py` (one file per line)

Source/Test lines are evidence pointers, not proof of compliance or passing tests.
Do not invent requirements, test results, publisher details or licensing terms.
Do not put private data in this document. A review never promotes draft to confirmed.

Bestätigte Anforderungen mit stabilen R-IDs und beobachtbaren Abnahmekriterien
festhalten. Source/Test sind Belegverweise, kein Nachweis bestandener Tests oder
fachlicher Erfüllung. Unbekanntes bleibt draft; keine privaten Daten eintragen.

## Current formats only / Nur aktuelle Formate

No legacy layouts, compatibility aliases, fallback discovery or automatic migrations.
Reject unsupported formats explicitly before writes; preserve all existing user data.
Changes to rules may make an existing plugin fail verification. Update it only under
an explicit implementation request; never weaken scope to accept outdated content.
Keine Altformat-Unterstützung oder stillen Migrationen. Nicht unterstützte Daten
mit konkretem Grund ablehnen, niemals löschen oder überschreiben.

## R1: Project-scoped operator language for generated plugins

Status: confirmed
Acceptance: This plugin ships a shared operator-language helper and entry-point instructions. Before setup/domain interaction, a missing project preference is asked alone and persisted only after an explicit answer. Later calls reuse it, including bare slash commands and new sessions. An explicit change updates only that project's preference. Content/documentation languages remain independent; invalid state is rejected without mutation. Future skills preserve the same gate.
Source: skills/_shared/scripts/operator_language.py
Source: skills/_shared/references/operator-language.md
