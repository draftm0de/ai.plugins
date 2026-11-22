export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
MARKETPLACE ?=
.PHONY: help test
help:
	@echo 'Tests: test (unit + integration + contracts), test-unit, test-integration, test-contracts, test-native, test-behavior'
	@echo 'Git + Python 3.10+; Make is optional. Use python3 -B scripts/verify.py or the relevant Python helper directly.'
	@echo 'Host CLI only for automatic local install. After edits/branch switches: install-local, then a new host session.'
	@echo 'configure is normal setup; local-marketplace.example.json is optional. Runtime reads ignored .local/marketplace.json only.'
	@echo 'make install-local TARGET=claude|codex  Test checkout edits without GitHub'
	@echo 'make sync-plugin / check-plugin     Generate / validate committed repository import metadata'
# Test layers: deterministic checks by default; native/model tests are explicit.
TEST_GROUP ?=
.PHONY: test test-unit test-integration test-contracts test-native test-behavior
test test-unit test-integration test-contracts test-native:
	$(PYTHON) -B scripts/run_tests.py --kind $(if $(filter test,$@),deterministic,$(patsubst test-%,%,$@)) $(if $(TEST_GROUP),--group "$(TEST_GROUP)",)
test-behavior:
	@echo "NOT RUN: no model behavior suite configured"

# Local development and repository metadata
# Disable implicit shell-script rules (for example install.sh -> install).
.SUFFIXES:
.PHONY: install-local check-plugin sync-plugin
install-local:
	$(PYTHON) scripts/plugin.py install-local --target "$(TARGET)" $(if $(MARKETPLACE),--marketplace "$(MARKETPLACE)",) $(if $(filter 1,$(DRY_RUN)),--dry-run,)
check-plugin:
	$(PYTHON) scripts/plugin.py check
sync-plugin:
	$(PYTHON) scripts/plugin.py sync
# End plugin commands

SOURCE ?= .
.PHONY: verify
verify:
	$(PYTHON) scripts/verify.py --source "$(SOURCE)" --kind auto $(if $(filter 1,$(REVIEW)),--review,)
