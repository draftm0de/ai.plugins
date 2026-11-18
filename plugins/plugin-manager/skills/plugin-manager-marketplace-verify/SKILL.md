---
name: plugin-manager-marketplace-verify
description: Read-only verification of a marketplace repository selected from the user's project context. Never repair files or execute target code.
---

# marketplace-verify

Use the repository path explicitly selected by the user or the current project root. Never substitute this installed plugin's folder. If the current working directory is unrelated, ask for the target repository. Run the bundled `../plugin-manager/scripts/verify.py --source TARGET --kind marketplace` with Python. A type mismatch is an error: explain it and suggest the matching action; do not switch targets silently. Report structural results separately from host acceptance and unverified remote contents. Do not repair, sync, install, commit or push during verification.
