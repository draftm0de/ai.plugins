# Storage and recovery

[Deutsch](../de/storage.md) | **English**

[Home](../../README.en.md) · [Overview](README.md) · [Install](installation.md) · [Use](usage.md) · [Screens](screens.md) · [FAQ](faq.md)

## Storage model

No domain storage model is implemented.

## Setup and configuration

Public manifests describe the plugin. Ignored .local/marketplace.json files hold machine-local marketplace associations and are not committed.

## Save and resume

There is no implemented user-session persistence. Development resumes from source and SCOPE.md.

## Failures and recovery

Preserve existing files and review conflicts. No automatic migration or recovery behavior is implemented.

## Limitations

Do not put private data in distributable skills or documentation. Future storage requirements must be confirmed before implementation.

---

Documentation prepared with Plugin Manager. Source-product ownership remains unchanged.
