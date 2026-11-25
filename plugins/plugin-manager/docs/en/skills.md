# Skills

[Deutsch](../de/skills.md) | **English**

<img src="../../assets/icon.png" alt="draftmode.io" width="48">

[Home](../../README.en.md) · [Installation](installation.md) · [Skills](skills.md) · [Concepts](concepts.md)

Five skills, one per task. In Claude Code you call them with `/plugin-manager:<skill>`.

## Overview

| Skill | Purpose |
| --- | --- |
| [docs](#docs) | Write documentation from the sources |
| [modify](#modify) | Change name, display name, description |
| [publish](#publish) | Publish under control |
| [setup](#setup) | Set up and keep current |
| [verify](#verify) | Check, read-only |

## docs

### Description

Writes or refreshes the documentation of a plugin or marketplace in the selected languages, from `SCOPE.md`, the skills and the source code.

### Workflow

1. Checks that the repository is set up.
2. Reads the sources and clarifies open points with you.
3. Writes README, installation, skills or plugin list, and concepts.
4. Checks structure and links.

### Example

`/plugin-manager:docs` after adding a skill: the skills page gets its section.

### Reads and writes

Reads the sources of the repository. Writes README and pages under `docs/`; your own existing text stays.


## modify

### Description

Changes what a repository says about itself: technical name, display name and description.

### Workflow

1. Checks that the repository is set up.
2. Asks what should change.
3. Shows every affected file without writing.
4. Writes only after your yes.

### Example

"Give the plugin the display name Interview Coach."

### Reads and writes

Reads the configuration and the associated marketplace. Writes the manifests and, for a plugin, its marketplace entry.


## publish

### Description

Prepares a publication and carries it out only with your approval, through a checked pull request.

### Workflow

1. Checks that the repository is set up.
2. Shows the diff, the commit message and the checks.
3. Waits for your approval.
4. Creates branch, commit, push and pull request.

### Example

"Prepare the documentation changes for publication."

### Reads and writes

Reads the diff and the Git facts. Writes to Git and GitHub only after approval; its journal lies outside the repository.


## setup

### Description

Brings a plugin or marketplace repository into the configured state and keeps the shared files current. Call it as often as you like.

### Workflow

1. Resolve the language.
2. Configure plugin or marketplace.
3. Add and update shared files; unchanged copies without a question, changed ones only by your decision.
4. One line "fully configured".

### Example

`/plugin-manager:setup` in an empty, cloned repository.

### Reads and writes

Reads the folder and the selected marketplace. Writes management files under `.project/`, the shared files and, when creating, the plugin skeleton.


## verify

### Description

Reports whether a repository follows the rules, and what is not yet proven.

### Workflow

1. Detects plugin or marketplace itself.
2. Checks structure and standards.
3. On request compares `SCOPE.md` with the source code.

### Example

`/plugin-manager:verify` before publishing.

### Reads and writes

Reads the repository. Writes nothing and runs no code of the repository.

---

Documentation prepared with Plugin Manager.
