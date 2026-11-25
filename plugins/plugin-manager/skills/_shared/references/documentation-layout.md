# Documentation layout

Structure and design of every documentation. How the texts sound is the repository's own `docs/style.md`; read it before writing and follow it where it does not contradict this file or the standards.

## Structure

Use a repeatable reader journey: understand (README) → install → look up each skill (workflow, example, what it reads and writes) → read the concepts. Use tables for parallel choices and numbered lists for sequential actions. Separate user tasks from developer internals.

The `templates/outline.json` filenames and level-two headings are the structural contract. Keep their order. Use level-three headings for project-specific detail; do not create empty sections. If a section does not apply, say so briefly with the factual reason. Put a consistent relative navigation row on each page under `docs/`.

Each language’s README remains compact: aim for 100–150 lines, linking deeper details rather than repeating them. Keep one top-level heading per page. Commands go in fenced blocks with the correct language. Provide the working directory and prerequisites; never introduce a command absent from source or verified host documentation.

## Visual system

Use the plugin's one icon `assets/icon.png` (never a copy) at width 48 in the README and documentation index of each language, with the alt text `draftmode.io`. Reference it with GitHub-compatible relative paths. A new plugin gets a neutral placeholder of 96 px that the plugin replaces by its own icon. Use native Markdown for tables and callouts. Optional repo-native SVG transcript previews use navy `#101b2d`, pale panels `#f4f7fc`, teal `#87ddc6`, dark text `#13243a` and a neutral sans-serif font. All previews require an explicit label and provenance in their page language; the design is not a host UI. Produce variants only for selected languages, with identical layout when bilingual. Never mix languages inside a generated graphic.

Use descriptive alt text. Include a visible text explanation for each visual. Do not invent a CI badge or license badge. A CI badge is allowed only when the actual remote and workflow exist. Documentation branding does not change source-product ownership.

## Boundaries

Describe verified local behavior separately from host platform acceptance. A created ZIP is not an installed or published plugin. Chat history is not automatically persistent writable state. Model examples and scores are illustrative, never guarantees. Documentation should be useful without reading the implementation.
