# Current-format policy / Aktuelle Formate

Status: confirmed

This scope records the approved compatibility boundary, not a complete product acceptance.

## R1: No backwards compatibility

Status: confirmed
Acceptance: Only current documented formats and entry points are supported. Reject obsolete formats without automatic inference, migration or modifying user data.
Source: scripts/marketplace.py
Test: tests/contracts/test_marketplace_catalogs.py
Test: tests/contracts/test_run_tests.py

The marketplace embeds no plugin; every plugin, the Plugin Manager included, has its own repository and SCOPE.md.
