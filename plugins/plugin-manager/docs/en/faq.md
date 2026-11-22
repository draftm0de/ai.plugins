# Faq

[Deutsch](../de/faq.md) | **English**

<img src="../assets/zyris-icon.png" alt="ZYRIS" width="48">

[Start](../../README.en.md) · [Guides](README.md)

## Product and access

The Manager bundles plugin-manager, marketplace-create, configure, update, verify and publish. The user confirmed imports from its GitHub repository in Claude and GPT.

## Requirements

Management tools require Git and Python 3.10+; Make is only a convenience wrapper. Management needs the selected host CLI only for automatic local installation/updates; explicitly requested model tests also need an authenticated CLI. Publish uses a sufficiently capable GitHub connector or alternatively authenticated gh; no GitLab MRs. First verify remote read, push, PR create/read, checks, rules and controlled merge capabilities and permissions. Report missing capabilities specifically; never install tools automatically. No additional Python packages, release Actions or version/tag requirements.

## Privacy and persistence

Exclude private CVs, state, credentials and unrelated work from documentation. Journals belong outside the plugin and source repositories.

## Troubleshooting

**Does `/plugin …` only open settings?** This behavior was observed in the Claude Desktop Code tab. Use the [graphical installation path](installation.md) there. Terminal slash commands do not establish that a desktop installation was performed.

For metadata drift run `make sync-plugin` and review the diff. For a missing update refresh the marketplace and open a new chat. An internal Codex label of 1.0.0 does not mean you must maintain a release version.

## Validation limits

Structural checks and successful import do not prove every feature, automatic updates or an entire publication run. ZIPs and tags are unnecessary for this installation path.
