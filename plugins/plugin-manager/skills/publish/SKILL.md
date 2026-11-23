---
name: publish
description: Prepare a reviewed diff and commit message, obtain approval, then publish through a checked GitHub PR with a verified base or a separately approved initial commit/direct push for an empty remote. No tags, releases or version proposal. Never publish during preparation.
---

# Publish a plugin

Read `../_shared/WORKFLOWS.md` and `../_shared/references/publish.md` before acting. This capability belongs to the single Plugin Manager plugin. Follow the **publish** routing and the mandatory approval boundary. A request to implement or prepare publish is not authorization to commit or publish. Use the bundled `../_shared/scripts/publish_plan.py` for the immutable local plan and progress journal. Do not require a Manager source checkout.

Read the initial-publication contract before handling an unborn HEAD. No automatic initial commits. PRs require an existing observed base branch. Schema-4 journals bind Codex metadata presence and bytes even outside selected files.

Regular publication: prepare → concrete approval → approved descriptive feature branch → commit → push → PR → checks → merge. No claude/ or codex/ prefix; never publish directly on the default branch except the separately approved empty-repository bootstrap. Use start-branch only after approval and reuse the verified journal-owned branch on resume. Read the canonical prerequisites and verify provider capabilities before preparing.

## State gate

Before preparing a plan follow `../_shared/flows/gate.md` (`setup_state.py gate`). When the gate is closed, stop with the reason and a pointer to `/plugin-manager:setup`; no plan, journal, branch or commit is created and publish writes nothing then.
