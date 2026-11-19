export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
SOURCE ?= .
.SUFFIXES:
.PHONY: help verify plugin-verify marketplace-verify sync-marketplace check-marketplace install-local update-local
help:
	@echo 'Tests: test (unit + integration + contracts), test-unit, test-integration, test-contracts, test-native, test-behavior'
	@echo 'Git + Python 3.10+; Make is optional. Use python3 -B scripts/verify.py or the relevant Python helper directly.'
	@echo 'Host CLI only for automatic local install/update. After edits/branch switches: update-local, then a new host session.'
	@echo 'configure is normal setup; local-marketplace.example.json is optional. Runtime reads ignored .local/marketplace.json only.'
	@echo 'verify / plugin-verify / marketplace-verify SOURCE=path: read-only structure + optional local availability'
	@echo 'sync-marketplace / check-marketplace: generate / check host catalogs'
	@echo 'install-local / update-local TARGET=claude|codex DRY_RUN=0|1: all associated local plugins'
verify plugin-verify marketplace-verify:
	$(PYTHON) scripts/verify.py --source "$(SOURCE)" --kind $(if $(filter plugin-verify,$@),plugin,$(if $(filter marketplace-verify,$@),marketplace,auto)) $(if $(filter 1,$(REVIEW)),--review,)
sync-marketplace:
	$(PYTHON) scripts/marketplace.py sync
check-marketplace:
	$(PYTHON) scripts/marketplace.py check
install-local update-local:
	$(PYTHON) scripts/local_plugins.py $@ --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)

# Test layers: deterministic checks by default; native/model tests are explicit.
TEST_GROUP ?=
.PHONY: test test-unit test-integration test-contracts test-native test-behavior
test test-unit test-integration test-contracts test-native:
	$(PYTHON) -B scripts/run_tests.py --kind $(if $(filter test,$@),deterministic,$(patsubst test-%,%,$@)) $(if $(TEST_GROUP),--group "$(TEST_GROUP)",)
test-behavior:
	@echo "NOT RUN: no model behavior suite configured"
