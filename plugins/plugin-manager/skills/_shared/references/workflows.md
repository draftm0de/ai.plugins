# Creation and association workflows

Use `python3 <plugin-root>/skills/_shared/scripts/workflows.py ACTION --help`. Run helpers from the installed skill, never execute helpers from an inspected target during verify. Paths come from the current user project or explicit input, not this installation. See [prerequisites.md](prerequisites.md): Git and Python 3.10+, optional Make, selected host CLI only for automatic local installation. No automatic installation of missing tools.

## Inputs and boundaries

Reuse confirmed session facts, existing manifests, documentation language policy and Git origin. Distinguish displayName from the lowercase kebab-case technical name. Do not infer publisher or license from a Git author. Never invent product instructions. plugin-create supports only explicit --skeleton; do not offer skill import. It creates only a nonfunctional, visibly marked entry point and pending SCOPE.md. Confirm domain requirements before implementing them. Never claim skeleton creation establishes a finished product.

Inspect existing files before any write. The helpers preflight collisions, preserve existing README/docs and licenses, and refuse differing owned-tool destinations. Configuration does not perform legacy migrations. Present conflicting files and resolve only within the user's authorized scope. Private content is never an input source. No action creates a GitHub repository, commits, pushes, installs or publishes implicitly.

## marketplace-create

The GitHub repository must already exist and be cloned. Example with fictional inputs:

```sh
python3 /path/to/installed/skills/_shared/scripts/workflows.py marketplace-create \
  --root /work/catalog --name example-plugins --display-name "Example Plugins" \
  --owner "Confirmed publisher"
```

Origin supplies the repository URL; --repository can check an explicit URL against it. Existing marketplace metadata supplies omitted names/owner; unknown facts require clarification. The result contains canonical marketplace.json, both derived host catalogs, standalone scripts, Makefile, DE/EN starter instructions and local-marketplace.example.json. No embedded manager or plugin is created. Existing identity conflicts stop creation. Repeating the same operation is idempotent.

## plugin-create (internal generator operation)

The public entry is `plugin-manager`; there is no separate plugin-create skill or slash command. Its saved operator-language gate and state routing govern this internal creation flow. The Python operation and its creation checks remain unchanged.

### Conversation language and licensing decisions

#### Guided interaction

Use a structured question tool when the current host exposes one (such as Claude's `AskUserQuestion`). Call the available tool according to its actual schema and limits; do not merely print its name or a numbered questionnaire. When no question tool is available in the current mode, state that briefly and ask one short question at a time in chat. Do not switch host modes, install tools or claim a dialog was displayed when it was not.

1. Use the saved operator language resolved by the central entry before configuration. Do not ask again or infer it from documentation settings or English instruction text. All questions, labels and reports use that language; technical identifiers stay unchanged. The central state check handles existing plugins without restarting creation. The internal generator independently rejects an existing product before license validation.

2. Create a skeleton only; do not ask for a creation mode or source skill path. Clarify a missing marketplace path. Translate choices to the resolved language. Reuse already confirmed paths and inspect only the authorized target and selected sources; do not explore unrelated sibling repositories to supply defaults.
3. Clarify missing identity fields, then documentation languages and their default. Suggestions from the target name must be labelled as suggestions requiring selection; do not infer publisher, language or license from neighboring repositories. Keep questions small and coherent rather than bundling all missing inputs into one form or message. Do not ask again for confirmed facts.
4. Resolve the license using the rules below. Offer choosing a specific license or explicitly deferring; request the actual license choice when needed, without recommending legal terms. An unanswered required question remains pending.
5. After the required answers are available, proceed within the user's creation authorization; do not add a redundant blanket approval question. Report actual checks and unresolved decisions after creation.

Documentation languages are resolved independently from the target's saved policy or the user's explicit choice; ask when missing or contradictory. They never change the operator language implicitly.

Resolve licensing before invoking the creation helper or writing target files. Reuse an explicit session decision or an unambiguous existing license in the target repository without asking again. If absent, ask which license should apply, with an explicit option to defer. Wait for an answer; absence of an answer is not permission to omit this step. Do not infer a license from the publisher, Git author, marketplace or neighboring repositories. Conflicting license files, metadata or user instructions require clarification before writes; preserve all existing content.

A deferred decision permits scaffolding but remains unresolved and must be named in the completion report. Pass it explicitly as `--license deferred`; omission is rejected before creation writes. The decision is persisted in `docs/license.md` and linked from each selected language's READMEs.

Implement a selected license instead of stopping at the decision. For MIT, pass `--license MIT --copyright-year YEAR --copyright-holder HOLDER` after confirming the copyright year and rights holder; do not infer them from the publisher or Git identity. The bundled MIT text is based on https://opensource.org/license/mit and preserves its terms. For another license, use its confirmed identifier with `--license-file /explicit/path/to/complete-text`; the agent must verify the text and identifier with the user or an authoritative source before invoking the helper. It copies the supplied text unchanged, without pretending to validate its legal meaning. Unsupported templates and incomplete text are rejected before writes. Do not invent license terms.

For an existing target license, use the confirmed identifier and that exact file as `--license-file`; preserve its bytes and name. Multiple license files or a differing selected text require review before writes. The helper creates the selected file when missing, writes the identifier to plugin.json and derived host metadata, and updates new documentation with the actual licensing state. Existing prose is preserved; missing decision links are reported for deliberate completion. Inspect `checks.licensing` and resolve errors before claiming licensing implementation is complete; deferred remains deferred, never implemented. No new approval is needed for the already confirmed license choice.

```sh
python3 /path/to/installed/skills/_shared/scripts/workflows.py plugin-create \
  --root /work/example-plugin --marketplace /work/catalog \
  --repository https://github.com/OWNER/EXISTING-REPO \
  --skeleton --name example-plugin --display-name "Example Plugin" \
  --description "Confirmed capability description" --author "Confirmed publisher" \
  --languages de en --default-language de --license deferred
```

Clone the existing remote when the target checkout is absent. Otherwise inspect the checkout and validate origin. The helper generates a nonfunctional skeleton skill and creates versionless plugin and host manifests, development tools, tests and documentation templates, registers the external repository in the marketplace and records local mappings. No marketplace catalogs belong in the plugin. Existing plugins use configure instead. A failed post-clone preflight leaves the cloned checkout available for inspection, without deleting it automatically.

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
  --languages de en --default-language de --license deferred
```

The GitHub repository already exists. Reuse origin or supply --repository for cloning.
--description is optional only for skeletons; the default explicitly says unimplemented.
No domain requirements, license or behavior are invented. SCOPE.md begins draft;
AGENTS.md, CLAUDE.md and docs/architecture.md keep common development rules available
in later chats. Existing differing files abort preflight rather than being overwritten.
The result reports implementation_status=skeleton; structural validity is independent.

New skeleton documentation is filled with localized scaffold facts and validated in staging before target writes. Existing prose is preserved; post-write `checks` report actual plugin/marketplace structure and documentation errors, including errors in preserved pages. `checks.status=passed` covers these checks plus technical consistency of the explicit licensing decision, files and documentation. It does not establish legal suitability, domain acceptance, executed tests or host acceptance. `needs_attention` means the creation workflow is not complete: report the findings and resolve them within authorization before claiming completion. The final agent report must state structure, documentation, the separately confirmed licensing decision and actual license files, pending implementation/acceptance, and actual test/host evidence separately.

Confirm SCOPE with the user, implement under skills/, add relevant tests, then request
verify with --review. The helper collects evidence; the agent compares actual source
and test logic with confirmed criteria. No tests are run by verify.

Creation rejects existing .claude/skills or .agents/skills before writing plugin files or associations. Skill import through plugin-create is unsupported; --source and --import are rejected before writes.
