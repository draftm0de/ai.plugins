# Creation and association workflows

Use `python3 <plugin-root>/skills/_shared/scripts/workflows.py ACTION --help`. Run helpers from the installed skill, never execute helpers from an inspected target during verify. Paths come from the current user project or explicit input, not this installation. See [prerequisites.md](prerequisites.md): Git and Python 3.10+, optional Make, selected host CLI only for automatic local installation. No automatic installation of missing tools.

## Inputs and boundaries

Reuse confirmed session facts, existing manifests, documentation language policy and Git origin. Distinguish displayName from the lowercase kebab-case technical name. Do not infer publisher or license from a Git author. Never invent product instructions. If there is no source skill, offer explicit --skeleton. It creates only a nonfunctional, visibly marked entry point and pending SCOPE.md. Confirm domain requirements before implementing them. With --source, preserve the supplied skill. Never claim skeleton creation establishes a finished product.

Inspect existing files before any write. The helpers preflight collisions, preserve existing README/docs and licenses, and refuse differing owned-tool destinations. Configuration does not perform legacy migrations. Present conflicting files and resolve only within the user's authorized scope. Private content is never an input source. No action creates a GitHub repository, commits, pushes, installs or publishes implicitly.

## marketplace-create

The GitHub repository must already exist and be cloned. Example with fictional inputs:

```sh
python3 /path/to/installed/skills/_shared/scripts/workflows.py marketplace-create \
  --root /work/catalog --name example-plugins --display-name "Example Plugins" \
  --owner "Confirmed publisher"
```

Origin supplies the repository URL; --repository can check an explicit URL against it. Existing marketplace metadata supplies omitted names/owner; unknown facts require clarification. The result contains canonical marketplace.json, both derived host catalogs, standalone scripts, Makefile, DE/EN starter instructions and local-marketplace.example.json. No embedded manager or plugin is created. Existing identity conflicts stop creation. Repeating the same operation is idempotent.

## plugin-create

```sh
python3 /path/to/installed/skills/_shared/scripts/workflows.py plugin-create \
  --root /work/example-plugin --marketplace /work/catalog \
  --repository https://github.com/OWNER/EXISTING-REPO \
  --source /work/agreed-skill --name example-plugin --display-name "Example Plugin" \
  --description "Confirmed capability description" --author "Confirmed publisher" \
  --languages de en --default-language de
```

Clone the existing remote when the target checkout is absent. Otherwise inspect the checkout and validate origin. The helper copies the source skill without renaming it, creates versionless plugin and host manifests, development tools, tests and documentation templates, registers the external repository in the marketplace and records local mappings. No marketplace catalogs belong in the plugin. Existing plugins use configure instead. A failed post-clone preflight leaves the cloned checkout available for inspection, without deleting it automatically.

The agent must complete missing documentation from the actual source, preserving existing prose, and run documentation validation. Scaffolding reports this outstanding step explicitly; structural success alone does not certify docs, licensing or product behavior. Do not invent license terms. Retain existing language choices; ask only when not established.

## configure

```sh
python3 /path/to/installed/skills/_shared/scripts/workflows.py configure \
  --root /work/existing-plugin --marketplace /work/catalog
```

Requires an existing valid plugin. Validate manifest identity against origin, register/update the external catalog entry and derive host catalogs. The marketplace's ignored `.local/marketplace.json` maps `sources.<plugin-name>` to a checkout. The plugin's ignored file stores `marketplace` as the local default and `marketplaces` as named associations. Paths are relative to the containing repository. Selecting a new default preserves previous associations and other catalog entries. Conflicting identities or checkout mappings require review; there is no silent reassignment or repair.

## Local development and verification

```sh
make verify
make install-local TARGET=claude
make update-local TARGET=codex
# From a plugin, override only this invocation:
make install-local TARGET=codex MARKETPLACE=/work/another-catalog
```

All selected marketplace plugins need local checkouts before installation. Preflight happens before snapshot replacement or host changes. No fallback to remote or one-plugin catalogs. Snapshots are filtered and generated under dist/local-development; DRY_RUN=1 still writes them. Never write host caches directly. Verify reports publishable structure independently from optional local completeness and never invokes repository code.

## Current entry points

Only marketplace-create, plugin-create and configure are accepted. init is unsupported. No automatic choice, migration or creation.

Before writing local associations, proposed root and `.local/.gitignore` rules are evaluated by real Git in an isolated repository. Global excludes cannot conceal unsafe repository rules. Negations that expose `.local/marketplace.json` cause an actionable error before either repository is written; existing rules, mappings and content remain unchanged. Review conflicting rules explicitly, then retry. Creation never makes initial commits. For a repository without HEAD, use the explicitly approved initial-publication mode in [publish.md](publish.md), or use an existing remote PR base.

Snapshots read the current checkout including uncommitted changes, regardless of branch. After changes or a branch switch, run update-local and open a new host session. Local testing requires no commit, push or PR and uses the same development marketplace across branches. configure is the normal setup path; local-marketplace.example.json is an optional manual copy template. Runtime reads only .local/marketplace.json; never commit local mappings.

## Skeleton first, implementation later

```sh
python3 /path/to/plugin/skills/_shared/scripts/workflows.py plugin-create \
  --root /work/new-plugin --marketplace /work/catalog --skeleton \
  --name example-plugin --display-name "Example Plugin" --author "Confirmed publisher" \
  --languages de en --default-language de
```

The GitHub repository already exists. Reuse origin or supply --repository for cloning.
--description is optional only for skeletons; the default explicitly says unimplemented.
No domain requirements, license or behavior are invented. SCOPE.md begins draft;
AGENTS.md, CLAUDE.md and docs/architecture.md keep common development rules available
in later chats. Existing differing files abort preflight rather than being overwritten.
The result reports implementation_status=skeleton; structural validity is independent.

Confirm SCOPE with the user, implement under skills/, add relevant tests, then request
verify with --review. The helper collects evidence; the agent compares actual source
and test logic with confirmed criteria. No tests are run by verify.

Creation rejects existing .claude/skills or .agents/skills before writing plugin files or associations. An explicitly selected standalone skill remains supported, but its frontmatter never bypasses existing documentation-manifest or obsolete-layout checks.
