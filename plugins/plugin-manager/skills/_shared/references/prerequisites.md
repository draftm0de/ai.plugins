# Voraussetzungen / Prerequisites

Diese Datei ist die kanonische Voraussetzungsliste für die Verwaltungswerkzeuge. Vorlagen übernehmen eine identische Kopie unter `docs/prerequisites.md`. Produkt- oder Host-spezifische Voraussetzungen müssen gesondert belegt werden.

This is the canonical prerequisite list for the management tools. Templates carry an identical copy at `docs/prerequisites.md`. Product-specific or host-specific requirements need separate evidence.

## Deutsch

- **Verwaltungswerkzeuge:** Git und Python 3.10 oder neuer; ausschließlich Python-Standardbibliothek, keine zusätzlichen Python-Pakete.
- **Make:** optionaler Komfortzugang. Die Python-Einstiegspunkte lassen sich direkt aufrufen; Make ist keine Voraussetzung für die Verwaltung.
- **Host-CLI:** nur für die automatische lokale Installation/Aktualisierung ist die gewählte Claude- oder Codex-CLI erforderlich. Snapshots mit `--dry-run`, Strukturprüfungen und Dokumentationswerkzeuge benötigen keine Host-CLI.
- **Optionale Modelltests:** ausdrücklich gestartete Review-Evaluationen benötigen eine authentifizierte Claude- oder Codex-CLI und können Credits verbrauchen. Sie gehören nicht zum normalen Testlauf.
- **Publish:** GitHub-only. Einen ausreichend leistungsfähigen GitHub-Connector verwenden; alternativ authentifiziertes `gh`. `gh` ist bei ausreichendem Connector nicht zusätzlich erforderlich. Keine GitLab-MR-Unterstützung.
- **Vor jeder Veröffentlichung:** Fähigkeiten und Rechte für das konkrete Repository prüfen und im Plan belegen: Remote/Default-Branch lesen (`remote_read`), pushen (`push`), PR erstellen und lesen (`pr_create`, `pr_read`), Checks und Branch-Regeln prüfen (`checks_read`, `rules_read`) und kontrolliert mit Schutz des geprüften Heads mergen (`merge`). Connector-Werkzeuge, Authentifizierung, Repository-Rechte und Regeln müssen die Schritte tatsächlich ermöglichen. Keine schreibenden Testaktionen zum Nachweis durchführen. Fehlende Rechte, menschliche Reviews oder Regeln nicht umgehen.
- **Fehlende Fähigkeiten:** konkret benennen, etwa „Branch-Regeln können mit diesem Connector nicht gelesen werden“; Veröffentlichung blockieren. Keine automatische Installation zusätzlicher Werkzeuge oder Änderung von Rechten. Der Journalhelfer prüft Nachweisfelder; der ausführende Agent muss die tatsächlichen Fähigkeiten prüfen. Ein Textnachweis ersetzt diese Beobachtung nicht.
- **Keine Release-Voraussetzungen:** keine Release-Actions, manuell gepflegten Manifest-Versionen, Versions-/Tag-Pflichten oder Plugin-ZIPs.

Die reguläre Veröffentlichung erfolgt nach konkreter Freigabe über einen aussagekräftigen separaten Feature-Branch ohne `claude/` oder `codex/`: Branch → Commit → Push → PR → Checks → Merge. Default- und Basisbranch dürfen nicht als Feature-Branch dienen. Der ausdrücklich freizugebende Bootstrap für vollständig leere Repositories ist die dokumentierte Ausnahme.

Lokale Snapshots verwenden den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR für lokale Tests; ein gemeinsamer `<marketplace-id>-dev`, keine zusätzlichen Marketplaces pro Branch.

`configure` ist der reguläre Einrichtungsweg. `local-marketplace.example.json` bleibt eine optionale manuelle Kopiervorlage. Zur Laufzeit wird ausschließlich `.local/marketplace.json` für lokale Zuordnungen gelesen. Diese Zuordnungen werden nicht committed. Vor dem Schreiben werden die wirksamen Ignore-Regeln geprüft.

Direkte Python-Aufrufe im jeweiligen Checkout (ohne Make):

```sh
python3 -B scripts/verify.py --source . --kind auto
# Marketplace:
python3 -B scripts/local_plugins.py install-local --target claude
# Plugin:
python3 -B scripts/plugin.py install-local --target codex
```

## English

- **Management tools:** Git and Python 3.10 or newer; Python standard library only, no additional Python packages.
- **Make:** optional convenience wrapper. Python entry points can be invoked directly; Make is not a management prerequisite.
- **Host CLI:** the selected Claude or Codex CLI is required only for automatic local installation/update. Snapshots with `--dry-run`, structural verification and documentation tooling need no host CLI.
- **Optional model tests:** explicitly started review evaluations require an authenticated Claude or Codex CLI and may consume credits. They are not part of the default test run.
- **Publication:** GitHub-only. Prefer a sufficiently capable GitHub connector; alternatively use authenticated `gh`. A capable connector does not additionally require `gh`. No GitLab MR support.
- **Before every publication:** verify and record capabilities and permissions for the selected repository: read remote/default branch (`remote_read`), push (`push`), create/read PRs (`pr_create`, `pr_read`), inspect checks/branch rules (`checks_read`, `rules_read`), and merge with control over the reviewed head (`merge`). Connector tools, authentication, repository permissions and rules must actually permit the steps. Do not perform test writes to prove permissions. Never bypass missing rights, required human reviews or branch rules.
- **Missing capabilities:** name the specific limitation, such as “this connector cannot read branch rules”, and block publication. Never install additional tools or change permissions automatically. The journal validates evidence fields; the executing agent must verify actual capabilities. Text evidence is not a substitute for observation.
- **No release prerequisites:** no release Actions, manually maintained manifest versions, version/tag requirements or plugin ZIPs.

Regular publication follows concrete approval using a descriptive separate feature branch without `claude/` or `codex/`: branch → commit → push → PR → checks → merge. Default/base branches cannot be the feature branch. Explicitly approved bootstrap for completely empty repositories remains the documented exception.

Local snapshots use the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. No commit, push or PR for local tests; one shared `<marketplace-id>-dev`, no additional marketplaces per branch.

`configure` is the normal setup path. `local-marketplace.example.json` remains an optional manual copy template. Only `.local/marketplace.json` is read for local runtime mappings. Never commit those mappings. Effective ignore rules are checked before writing.

Direct Python commands in the relevant checkout (without Make):

```sh
python3 -B scripts/verify.py --source . --kind auto
# Marketplace:
python3 -B scripts/local_plugins.py install-local --target claude
# Plugin:
python3 -B scripts/plugin.py install-local --target codex
```
