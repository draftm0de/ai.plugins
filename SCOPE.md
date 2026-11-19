# Current-format policy / Aktuelle Formate

Status: confirmed

This scope records the approved compatibility boundary, not a complete product acceptance.

## R1: No backwards compatibility

Status: confirmed
Acceptance: Only current documented formats and entry points are supported. Reject obsolete formats without automatic inference, migration or modifying user data.
Source: scripts/marketplace.py
Test: tests/contracts/test_current_policy.py
Test: tests/contracts/test_marketplace.py
Test: tests/unit/test_test_runner.py

The embedded Manager has its own SCOPE.md under plugins/plugin-manager; it remains the explicitly approved existing exception.
