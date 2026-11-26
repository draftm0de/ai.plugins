# Voraussetzungen / Prerequisites

Diese Datei ist die kanonische Voraussetzungsliste für die Verwaltungswerkzeuge. Vorlagen übernehmen eine identische Kopie unter `docs/prerequisites.md`. Produkt- oder Host-spezifische Voraussetzungen müssen gesondert belegt werden.

This is the canonical prerequisite list for the management tools. Templates carry an identical copy at `docs/prerequisites.md`. Product-specific or host-specific requirements need separate evidence.

## Deutsch

- **Verwaltungswerkzeuge:** Git und Python 3.10 oder neuer; ausschließlich Python-Standardbibliothek, keine zusätzlichen Python-Pakete.
- **Make:** optionaler Komfortzugang. Die Python-Einstiegspunkte lassen sich direkt aufrufen; Make ist keine Voraussetzung für die Verwaltung.
- **Host-CLI:** nur für die automatische lokale Installation/Aktualisierung ist die gewählte Claude- oder Codex-CLI erforderlich. Snapshots mit `--dry-run`, Strukturprüfungen und Dokumentationswerkzeuge benötigen keine Host-CLI.
- **Optionale Modelltests:** ausdrücklich gestartete Review-Evaluationen benötigen eine authentifizierte Claude- oder Codex-CLI und können Credits verbrauchen. Sie gehören nicht zum normalen Testlauf.
- **Veröffentlichen:** Du committest und pushst selbst; installiert wird, was auf dem Standard-Branch liegt. Keine Releases, Manifest-Versionen, Tags oder Plugin-ZIPs.

Lokale Snapshots verwenden den aktuellen Checkout einschließlich uncommitteter Änderungen, unabhängig vom Branch. Nach Änderungen oder Branchwechsel `install-local` ausführen und eine neue Host-Sitzung öffnen. Kein Commit, Push oder PR für lokale Tests; ein gemeinsamer `<marketplace-id>-dev`, keine zusätzlichen Marketplaces pro Branch.

Die lokale Zuordnung eines Plugins zu seinem einen Marketplace richtet plugin-manager (associate) ein und ändert sie. Der Marketplace-Pfad eines Plugins wird ausschließlich aus der von Git ignorierten `.project/plugins/plugin-manager/local.json` gelesen, die Checkouts der Plugins ausschließlich aus der `.local/marketplace.json` des Marketplace; `local-marketplace.example.json` bleibt eine optionale manuelle Kopiervorlage. Diese Zuordnungen werden nicht committed. Vor dem Schreiben werden die wirksamen Ignore-Regeln geprüft.

Direkte Python-Aufrufe im jeweiligen Checkout (ohne Make):

```sh
python3 -B scripts/verify/structure.py --source .
python3 -B scripts/verify/standards.py --source .
python3 -B scripts/verify/docs.py --source .
# only in the marketplace:
python3 -B scripts/local_plugins.py install-local --target claude
```

## English

- **Management tools:** Git and Python 3.10 or newer; Python standard library only, no additional Python packages.
- **Make:** optional convenience wrapper. Python entry points can be invoked directly; Make is not a management prerequisite.
- **Host CLI:** the selected Claude or Codex CLI is required only for automatic local installation/update. Snapshots with `--dry-run`, structural verification and documentation tooling need no host CLI.
- **Optional model tests:** explicitly started review evaluations require an authenticated Claude or Codex CLI and may consume credits. They are not part of the default test run.
- **Publishing:** you commit and push yourself; what lies on the default branch is installed. No releases, manifest versions, tags or plugin ZIPs.

Local snapshots use the current checkout including uncommitted changes, regardless of branch. After edits or branch switches run `install-local` and open a new host session. No commit, push or PR for local tests; one shared `<marketplace-id>-dev`, no additional marketplaces per branch.

The local association of a plugin with its one marketplace is set up and changed by plugin-manager (associate). The marketplace path of a plugin is read only from the Git-ignored `.project/plugins/plugin-manager/local.json`, the checkouts of the plugins only from the marketplace's `.local/marketplace.json`; `local-marketplace.example.json` remains an optional manual copy template. Never commit those mappings. Effective ignore rules are checked before writing.

Direct Python commands in the relevant checkout (without Make):

```sh
python3 -B scripts/verify/structure.py --source .
python3 -B scripts/verify/standards.py --source .
python3 -B scripts/verify/docs.py --source .
# only in the marketplace:
python3 -B scripts/local_plugins.py install-local --target claude
```
