# Entwicklung / Development

[Deutsch](#deutsch) · [English](#english) · [README](../README.md)

## Deutsch

So pflegst du den Katalog. Du brauchst Git und Python 3.10+. Make ist nur eine Abkürzung. Alle Befehle laufen im Stamm dieses Repositorys.

### Katalog ändern

`marketplace.json` ist die einzige Quelle des Katalogs. Daraus entstehen die Kataloge für Claude und Codex. Nach einer Änderung erzeugst und prüfst du sie:

```sh
make sync-marketplace
make check-marketplace
```

Jeder Eintrag nennt `name`, `displayName`, `description` und `repository`. Eingebettete Plugins und feste Versionen werden abgelehnt.

### Prüfen und testen

```sh
make verify
make test
```

`make verify` liest nur. `make test` führt Unit-, Integrations- und Vertragstests aus. Mehr dazu steht in der [Testübersicht](../tests/README.md).

### Lokal ausprobieren

Die Pfade zu den Plugin-Checkouts stehen unter `sources` in `.local/marketplace.json`. Git ignoriert diese Datei. Der Plugin Manager trägt sie beim Zuordnen eines Plugins ein; [local-marketplace.example.json](../local-marketplace.example.json) zeigt das Format. Jedes gelistete Plugin braucht einen lokalen Checkout.

```sh
make install-local TARGET=claude
```

Für Codex nimmst du `TARGET=codex`. Das installiert Snapshots (gefilterte Kopien deiner Checkouts, auch mit uncommitteten Änderungen) im Marketplace `draftmode-ai-plugins-dev`. Mit `DRY_RUN=1` entstehen nur die Snapshots, ohne Aufruf von Claude oder Codex. Öffne danach eine neue Sitzung.

### Veröffentlichen

Veröffentliche zuerst das Plugin in seinem Repository, danach den Eintrag hier. In Claude Code startest du dafür `/plugin-manager:publish`. Es fragt vor jeder Veröffentlichung nach deiner Freigabe.

## English

This is how you maintain the catalogue. You need Git and Python 3.10+. Make is only a shortcut. All commands run in the root of this repository.

### Change the catalogue

`marketplace.json` is the only source of the catalogue. The catalogues for Claude and Codex are generated from it. After a change, generate and check them:

```sh
make sync-marketplace
make check-marketplace
```

Each entry names `name`, `displayName`, `description` and `repository`. Embedded plugins and pinned versions are rejected.

### Check and test

```sh
make verify
make test
```

`make verify` only reads. `make test` runs unit, integration and contract tests. See the [test guide](../tests/README.md).

### Try it locally

The paths to the plugin checkouts are listed under `sources` in `.local/marketplace.json`. Git ignores this file. The Plugin Manager writes it when you associate a plugin; [local-marketplace.example.json](../local-marketplace.example.json) shows the format. Every listed plugin needs a local checkout.

```sh
make install-local TARGET=claude
```

Use `TARGET=codex` for Codex. This installs snapshots (filtered copies of your checkouts, including uncommitted changes) in the marketplace `draftmode-ai-plugins-dev`. With `DRY_RUN=1` only the snapshots are written, without calling Claude or Codex. Open a new session afterwards.

### Publish

Publish the plugin in its own repository first, then the entry here. In Claude Code, run `/plugin-manager:publish`. It asks for your approval before anything is published.
