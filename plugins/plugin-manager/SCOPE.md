# Current-format policy / Aktuelle Formate

Status: confirmed

This scope records the approved compatibility boundary, not a complete product acceptance.

## R1: No backwards compatibility

Status: confirmed
Acceptance: Only current documented formats and entry points are supported. Reject obsolete formats without automatic inference, migration or modifying user data.
Source: skills/_shared/WORKFLOWS.md
Source: scripts/plugin.py
Source: skills/_shared/scripts/workflows.py
Source: skills/_shared/scripts/documentation.py
Test: tests/integration/update/test_documentation.py
Test: tests/integration/plugin_create/test_workflows.py
Test: tests/integration/test_shared_installer.py
