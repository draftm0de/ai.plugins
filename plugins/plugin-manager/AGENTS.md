<!--
This file comes from the plugin manager and is managed by it: do not edit it here, changes are overwritten or reported.
Write your plugin's own instructions in CUSTOM.AGENTS.md.
Diese Datei stammt vom Plugin-Manager und wird von ihm verwaltet: hier nicht ändern, Änderungen werden überschrieben oder gemeldet.
Eigene Anweisungen gehören in CUSTOM.AGENTS.md.
-->

# Development rules / Entwicklungsregeln

Read SCOPE.md and docs/architecture.md before implementation. Clarify missing or
contradictory requirements; never infer product requirements from existing code.
Keep confirmed scope separate from implementation evidence. Preserve unrelated edits.

Implement plugin runtime under skills/<skill>/; shared runtime may live under
skills/_shared/ without a SKILL.md. Root scripts/ contains development tooling only.
Marketplace repositories own catalogs; plugin repositories never own catalogs.
Follow the layered tests described in tests/README.md. Add acceptance tests for
confirmed requirements. Generated structural tests do not establish product behavior.

Use verify for read-only checks and its explicit --review mode for scope/source
review. Do not execute target code as part of review. Run tests only as a separately
authorized development step and report actual results. Do not change scope to hide
implementation gaps. Never read private workspaces, credentials or ignored personal data.
Do not install tools, commit, push or publish without the corresponding authorization.

Vor Implementierung SCOPE.md und docs/architecture.md lesen. Fehlende Anforderungen
klären; fachliche Lücken nicht durch nachträgliche Soll-Änderungen verstecken.
Tests und Review getrennt behandeln. Bestehende Arbeit und private Daten erhalten.

## Current formats only / Nur aktuelle Formate

No legacy layouts, compatibility aliases, fallback discovery or automatic migrations.
Reject unsupported formats explicitly before writes; preserve all existing user data.
Changes to rules may make an existing plugin fail verification. Update it only under
an explicit implementation request; never weaken scope to accept outdated content.
Keine Altformat-Unterstützung oder stillen Migrationen. Nicht unterstützte Daten
mit konkretem Grund ablehnen, niemals löschen oder überschreiben.

## Operator language

Every public skill must load `skills/_shared/references/operator-language.md` before
setup/domain interaction. Preserve this gate when replacing the skeleton or adding
skills. Persist the explicit preference per consuming project; never in the plugin.

## Standards / Standards

Before implementing, read `docs/standards/coding.md`, `messages.md`, `testing.md` and `skills.md`. They are
managed by the plugin manager and identical in every plugin: never edit them here, never copy their text into
SCOPE.md and never deviate from them. SCOPE.md holds only the goal and requirements of this plugin; when it
contradicts a standard, the standard wins and `verify` reports the contradiction.

Vor der Implementierung `docs/standards/coding.md`, `messages.md`, `testing.md` und `skills.md` lesen. Sie
werden vom Plugin-Manager verwaltet und sind in jedem Plugin gleich: hier nicht ändern, nicht in SCOPE.md
kopieren, nicht davon abweichen. SCOPE.md enthält nur Ziel und Anforderungen dieses Plugins; bei einem
Widerspruch gilt der Standard und `verify` meldet ihn.

## Plugin-specific instructions / Plugin-spezifische Anweisungen

Also read `CUSTOM.AGENTS.md` when it exists. It holds only what is specific to this plugin and never repeats or
weakens a rule of this file or of the standards. This file is managed by the plugin manager: do not edit it here.

Lies außerdem `CUSTOM.AGENTS.md`, falls vorhanden. Sie enthält nur Plugin-Spezifisches und wiederholt oder
schwächt keine Regel dieser Datei oder der Standards. Diese Datei wird vom Plugin-Manager verwaltet: hier nicht ändern.

Imports for Claude Code (other hosts read the files named above as text) / Importe für Claude Code:

@CUSTOM.AGENTS.md
@docs/standards/coding.md
@docs/standards/messages.md
@docs/standards/testing.md
@docs/standards/skills.md
