# Draftmode AI Plugins

[Deutsch](README.md) | **English**

Marketplace `draftmode-ai-plugins`, displayed as **Draftmode AI Plugins**. Repository: https://github.com/draftm0de/ai.plugins

| Plugin | Identifier | Source |
| --- | --- | --- |
| [Plugin Manager](plugins/plugin-manager/README.en.md) | plugin-manager | Existing embedded exception: plugins/plugin-manager |
| [Interview Coach](https://github.com/draftm0de/ai.plugin.interview-coach) | interview-coach | Separate repository |

## Skills and their responsibilities

`plugin-manager` is the plugin bundling four skills. Select the appropriate skill for your target repository. Shared rules, tools and templates live under [`skills/_shared/`](plugins/plugin-manager/skills/_shared/WORKFLOWS.md); there is no separate Manager skill.

| Skill | Responsibility |
| --- | --- |
| [plugin-manager](plugins/plugin-manager/skills/plugin-manager/SKILL.md) | Central entry: set up the language, configure a plugin or a marketplace, synchronize the skeleton and change the marketplace association of a plugin. |
| [verify](plugins/plugin-manager/skills/verify/SKILL.md) | Detect repository type and inspect it read-only. Assess publishable structure separately from available local development configuration. |
| [update](plugins/plugin-manager/skills/update/SKILL.md) | Maintain README and documentation from current sources and saved language settings. No installation or publication. |
| [publish](plugins/plugin-manager/skills/publish/SKILL.md) | Plan publication for a plugin or marketplace. Execute through feature branch, commit, push, PR, checks and merge only after concrete approval. |

`plugin-verify` and `marketplace-verify` remain explicit verification commands, not separate skills. `init` is not supported; use plugin-manager explicitly.

### Usage and boundaries

In Claude Code use, for example, `/plugin-manager:plugin-manager`, `/plugin-manager:verify`, `/plugin-manager:update`, `/plugin-manager:publish`. In Codex select the currently named skill or describe the task and target repository. [Inputs and examples](plugins/plugin-manager/docs/en/usage.md).

`update` maintains documentation. `install-local` builds and refreshes local plugin snapshots including uncommitted changes. Metadata synchronization and documentation validation are tool functions, not additional skills. Create does not create a GitHub repository or invent domain skill content. Publish treats plugin and marketplace separately; explicitly approved bootstrap of completely empty repositories remains the documented exception to the PR workflow.

**Interview Coach** bundles the `interview-coach` skill for interview practice, targeted preparation, feedback and optional private learning progress. It belongs to the separate plugin repository; [responsibilities and modes](https://github.com/draftm0de/ai.plugin.interview-coach/blob/main/README.en.md#capabilities-and-modes).

## Installation

Add `https://github.com/draftm0de/ai.plugins` as a marketplace in the host plugin management UI and select a plugin. Repository installation requires no plugin ZIP, tag or manually maintained manifest version. See [installation](plugins/plugin-manager/docs/en/installation.md). Refresh the marketplace and open a new session after updates; CLI tests do not prove desktop/account synchronization.

## Development

This handbook covers the path from a local checkout to publication. `ai.plugins` manages the marketplace; each new plugin gets a separate repository. The existing `plugin-manager` under `plugins/plugin-manager/` remains the only embedded exception.

- [Marketplace](#marketplace): [Create/set up](#marketplace-create) · [Maintain and verify the catalog](#marketplace-verify) · [Publish](#marketplace-publish) · [Documentation](#marketplace-documentation)
- [Plugin](#plugin): [Create/set up](#plugin-create) · [Install locally](#plugin-local) · [Test](#plugin-test) · [Documentation](#plugin-documentation) · [Publish](#plugin-publish)

**Prerequisites:** Git and Python 3.10+; Make is a convenience wrapper. Automatic local installation and updates require the selected Claude/Codex CLI; model tests also require authentication. Management tools need no additional Python packages. [All prerequisites](plugins/plugin-manager/skills/_shared/references/prerequisites.md).

**Working in chat:** First add the marketplace and install **Plugin Manager**, making it available in the session. Use a local Claude/Codex environment with access to your project files and development tools. Create or open a project, select the repository folder as the working directory, and start a chat there. Project selection varies by host; what matters is the local target folder. Installing the plugin alone does not give a web-only chat access to your checkout.

In Claude Code, start the corresponding command, such as `/plugin-manager:plugin-manager`; in Codex, select the skill or explicitly name it in your request. Provide any additional repository paths in chat. The target is your selected project or an explicitly specified folder, never automatically the Manager installation directory.

**Working in the terminal:** The Create examples require a local `ai.plugins` checkout and run from its root. Installing the Manager alone does not provide that Makefile in your project. Other commands run in the repository indicated. Replace placeholders such as `../my-plugin` and publisher details with your own values. Chat workflows use the same tools and require the same technical prerequisites.

### Marketplace

<a id="marketplace-create"></a>

#### Create/set up

**In chat**

1. Create a GitHub repository and clone it locally.
2. Create or open a Claude/Codex project for that checkout and select its folder.
3. Start a new chat with Plugin Manager available.
4. Select `plugin-manager` or run `/plugin-manager:plugin-manager` in Claude Code and choose “marketplace” as the kind.
5. Supply the technical identifier, display name and publisher. Known project details and Git origin are reused; missing or conflicting details are clarified.

> Run plugin-manager as a marketplace in the selected project folder. Use my-catalog as the identifier, “My Catalog” as the display name and “Confirmed Publisher” as the publisher. Set up the marketplace and verify its structure afterward.

**In the terminal** — from the `ai.plugins` checkout:

```sh
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py marketplace-create --root ../my-marketplace --name my-catalog --display-name "My Catalog" --owner "Confirmed Publisher"
```

This creates `marketplace.json`, Claude and Codex host catalogs, standalone tools, a Makefile and documentation scaffolding. New marketplaces do not need an embedded Manager. Existing content is inspected first; differing files are not silently overwritten.

To work on **this** marketplace, do not run Create again. Associate existing plugin checkouts through `plugin-manager` (associate); add new plugins with `plugin-manager`, as described in the [Plugin section](#plugin-create).

<a id="marketplace-verify"></a>

#### Maintain and verify the catalog

`marketplace.json` is the canonical catalog configuration. After changes, generate and check the host catalogs.

**In chat:** Open the marketplace project and request each step explicitly:

> Synchronize this marketplace’s host catalogs, check them with verify, then run the regular tests. Report structural checks and test results separately.

`verify` alone does not run tests or synchronize files.

**In the terminal** — from the relevant marketplace root:

```sh
python3 -B scripts/marketplace.py sync
python3 -B scripts/marketplace.py check
python3 -B scripts/verify.py --source .
make test
```

In `ai.plugins`, `make sync-plugin` and `make check-plugin` also handle the embedded Manager’s metadata. Root `make test` runs both marketplace and Manager tests.

Local checkout paths live under `sources` in the Git-ignored `.local/marketplace.json`. The association of a plugin is set up and changed by `plugin-manager` (associate); a plugin stores the path of its one marketplace in the Git-ignored `.project/plugins/plugin-manager/local.json`. Optionally use `local-marketplace.example.json` as a manual copy template; relative paths start at the marketplace root.

Verification separates `structure_valid` from `local_development.complete`: a fresh clone may be structurally valid without local mappings. Local installation requires all necessary plugin checkouts. [Local installation](#plugin-local) · [Test guide](tests/README.md).

<a id="marketplace-publish"></a>

#### Publish

**In chat**

1. Open the marketplace project.
2. Select the marketplace folder as the working directory.
3. Start a new chat with Plugin Manager available.
4. Select `publish` or run `/plugin-manager:publish` in Claude Code.

Request: “Run publish for this marketplace and prepare the publication plan for approval.” The workflow is preparation, concrete approval including the feature branch name, branch, commit, push, PR, checks and merge. Publish requires a sufficiently capable GitHub connector or authenticated `gh` with the necessary permissions.

Publish and verify new or changed plugin sources in their own repositories before publishing the corresponding marketplace entry. Plugin and marketplace receive separate publication plans. Explicitly approved bootstrap of a completely empty repository is the documented exception to the PR workflow.

After publication, refresh the marketplace in Claude or Codex and check the offered plugins. This catalog should offer installable **Plugin Manager** and **Interview Coach** entries. The Coach is referenced through its repository’s default branch without a tag or version pin; both repositories must be accessible. Local CLI tests do not replace GitHub/GUI acceptance.

No release Actions, tags or plugin ZIPs are required. [Approval and resumption](plugins/plugin-manager/docs/en/publish.md).

<a id="marketplace-documentation"></a>

#### Documentation

Marketplace READMEs describe the catalog, installation and development workflows.

**In chat**

1. Open the marketplace project.
2. Select the marketplace folder as the working directory.
3. Start a new chat with Plugin Manager available.
4. Select `update` or run `/plugin-manager:update` in Claude Code.

Request: “Run update for ai.plugins, then check both READMEs for content accuracy and local links.” Sources are reread and existing language editions are maintained.

```sh
# From the ai.plugins root:
make validate-docs
```

This command validates the embedded Manager’s documentation. Also review the marketplace READMEs for content and local links. Detailed Manager guides live under [`plugins/plugin-manager/docs/`](plugins/plugin-manager/docs/en/README.md).

### Plugin

<a id="plugin-create"></a>

#### Create/set up

A new plugin belongs in a separate GitHub repository with its own manifests, skills and documentation. It does not contain a marketplace catalog. The GitHub repository must already exist; a missing local checkout can be cloned using `--repository`.

**In chat**

1. Create a separate GitHub repository for the plugin. To select it directly as a project, clone it locally and open the checkout as a new Claude/Codex project.
2. Select the plugin folder as the working directory. Have the local marketplace path ready; the installed catalog does not replace a marketplace checkout.
3. Start a new chat with Plugin Manager available.
4. Select `plugin-manager` or run `/plugin-manager:plugin-manager` in Claude Code. Creation produces only an unfinished skeleton.
5. Provide names, publisher, marketplace and documentation languages where these are not already known from the project.

> Run plugin-manager for this project in skeleton mode. Use the marketplace at ../my-marketplace, my-plugin as the identifier, “My Plugin” as the display name and “Confirmed Publisher” as the publisher. Document in German and English, with German as the default. Then work with me to confirm the intended scope in SCOPE.md.

Open the explicitly selected plugin checkout as the project before starting the central entry.

**In the terminal** — choose one source mode for a new plugin:

| Starting point | Option | Result |
| --- | --- | --- |
| Import an existing skill | `--source ../my-skill` | Copies the confirmed skill. |
| Domain implementation has not started | `--skeleton` | Creates a nonfunctional scaffold with a pending `SCOPE.md`. |

Example for a skeleton in an already cloned repository:

```sh
# From the ai.plugins root:
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py plugin-create --root ../my-plugin --marketplace . --skeleton --name my-plugin --display-name "My Plugin" --author "Confirmed Publisher" --languages de en --default-language de
```

Skill import is unsupported. `python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py plugin-create --help` lists all options.

`plugin-create` creates development tools and documentation templates, registers the plugin in the marketplace and sets up local mappings. For a skeleton, then confirm the scope in `SCOPE.md`, implement the skills and add relevant tests. Structural validity alone does not establish a finished product.

A plugin belongs to exactly one marketplace. To set up its association again (fresh clone, moved checkout) or to move it to another marketplace, use the `associate` flow of `plugin-manager`.

**In chat**

1. Open the plugin project.
2. Select the plugin folder as the working directory.
3. Start a new chat with Plugin Manager available.
4. Run `/plugin-manager:plugin-manager` in Claude Code and ask to change the marketplace association.

For example, request:

> Change the marketplace association of this plugin to the marketplace at ../my-marketplace.

Alternatively, from the `ai.plugins` checkout in the terminal:

```sh
python3 -B plugins/plugin-manager/skills/_shared/scripts/workflows.py associate --root ../my-plugin --marketplace .
```

The plugin's identity `marketplace {name, repository}` is stored in its committed `.project/plugins/plugin-manager/config.json`, the path of the checkout in the Git-ignored `.project/plugins/plugin-manager/local.json`; the marketplace keeps the checkouts of its plugins under `sources` in its `.local/marketplace.json`. Changing the marketplace moves the catalog entry in one transaction; local paths are not committed. [Create/Associate guide](plugins/plugin-manager/docs/en/usage.md) · [Technical options](plugins/plugin-manager/skills/_shared/references/workflows.md).

<a id="plugin-local"></a>

#### Install locally

**In chat:** Open the plugin or marketplace project and specify the host:

> Use install-local to make the associated plugins available in Codex from their local checkouts.

After edits or a branch switch:

> Use install-local to refresh the local plugin snapshots for Codex, including my uncommitted changes.

For Claude, specify “for Claude” instead. `install-local` is a tool action, not a separate skill or slash command. The agent runs the repository tools; the selected host CLI must be available.

**In the terminal** — after configuration, from the marketplace or configured plugin repository:

```sh
make install-local TARGET=claude
# Alternatively, for Codex:
make install-local TARGET=codex
```

Installation creates filtered snapshots under `dist/local-development/` and installs **all associated plugins** in the shared `<marketplace-id>-dev`. For this marketplace, the name is `draftmode-ai-plugins-dev`. All required checkouts must be available before the host call.

Refresh snapshots after changes or a branch switch:

```sh
make install-local TARGET=claude
# Alternatively, for Codex:
make install-local TARGET=codex
```

Then open a new host session and activate the intended development copy. Snapshots include uncommitted edits; local tests require no commit, push or PR. No additional marketplace is created for each branch.

| Option | Effect |
| --- | --- |
| `DRY_RUN=1` | Writes snapshots and shows commands without calling the host. |

Earlier `plugin-manager-dev` installations are not removed automatically. Disable or remove old copies after successful verification. CLI installation does not establish automatic synchronization with a desktop/web account interface.

<a id="plugin-test"></a>

#### Test

**In chat:** Open the plugin project and distinguish structural checks, tests and semantic review:

> Synchronize and check the plugin metadata. Run verify for this plugin, then run the regular tests. Report the results separately.

For semantic review, also request: “Use verify to review the implementation against the confirmed SCOPE.md.” Request native host tests or model tests separately and specify the host. In Claude Code, `/plugin-manager:verify` starts only the read-only check; tests need an additional request.

**In the terminal** — from the plugin repository:

```sh
make sync-plugin
make check-plugin
make verify
make test
```

`make verify` detects the repository type and reads structure and available local mappings. It runs no tests, repairs or target scripts. From `ai.plugins`, explicitly check a separate plugin with:

```sh
make verify SOURCE=../my-plugin
```

| Check | Command | What it establishes |
| --- | --- | --- |
| Unit, integration and contract tests | `make test` | Checks implemented functions, tool workflows and contracts. |
| Native host tests, where available | `make test-native` | Checks local installation and updates with isolated host profiles. |
| Model tests, where configured | `make test-behavior` | Checks behavior through real model calls; may consume credits. |
| Scope/source review | `make verify REVIEW=1`, followed by agent review | Collects static evidence for comparison with confirmed requirements; runs no tests. |

Native tests and model tests are started separately. Missing suites report `NOT RUN`, which is not a passing result. In the Manager, explicitly start model tests with `make test-behavior CLI=claude` or `CLI=codex`. The [test guide](tests/README.md) explains test types and available suites.

After automated checks, test the plugin’s actual behavior in a new host session. Installation from the published marketplace remains a separate acceptance step.

<a id="plugin-documentation"></a>

#### Documentation

Update the plugin documentation after functional changes.

**In chat**

1. Open the plugin project.
2. Select the plugin folder as the working directory.
3. Start a new chat with Plugin Manager available.
4. Select `update` or run `/plugin-manager:update` in Claude Code.

Request: “Run update for my-plugin. Update the documentation from the current sources and validate it afterward.” Create provides scaffolding; complete the content from actual capabilities.

The language policy in `docs/documentation.json` controls README and guide languages. The Manager uses German and English, with German as the default. Validate its documentation from the `ai.plugins` root with:

```sh
make -C plugins/plugin-manager validate-docs OUTPUT=.
```

For other plugins, use their documented validator. Supplement structural and link checks with a content review. `update` maintains documentation; `install-local` refreshes installed development snapshots. Neither action publishes changes. [Manager development guide](plugins/plugin-manager/docs/en/development.md).

<a id="plugin-publish"></a>

#### Publish

Before publication, complete implementation, tests and documentation in the plugin repository.

**In chat**

1. Open the plugin project.
2. Select the plugin folder as the working directory.
3. Start a new chat with Plugin Manager available.
4. Select `publish` or run `/plugin-manager:publish` in Claude Code.
5. Request: “Use publish to prepare this plugin’s publication and present the concrete plan for approval.”
6. After approval, proceed through feature branch, commit, push, PR, checks and merge.
7. If the marketplace entry is new or changed, then [publish the marketplace](#marketplace-publish).
8. Refresh the marketplace in the host, open a new session and test the published plugin’s behavior.

Publish plugin sources before the marketplace entry. Repository installation requires no plugin ZIPs or tags. See the [publication guide](plugins/plugin-manager/docs/en/publish.md) for approval, checks and resumption.

## Migration

The working state of `zyris.skill.manager`, including uncommitted changes, was copied to `plugins/plugin-manager`. This repository is the canonical source; the old local repository remains a backup and is not maintained in parallel. Its Git history and personal IDE settings were not copied.

The technical plugin identity is now `plugin-manager`. Existing installations are not renamed automatically. Install the new entry and disable the old copy after successful verification. Confirmation of the earlier import is not an acceptance test of this marketplace.
