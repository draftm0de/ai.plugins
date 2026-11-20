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
