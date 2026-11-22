export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
SOURCE ?= .
PLUGIN_DIR := plugins/plugin-manager
.SUFFIXES:
.PHONY: help sync-plugin check-plugin test verify validate-docs install-local
help:
	@echo 'Tests: test (unit + integration + contracts), test-unit, test-integration, test-contracts, test-native, test-behavior'
	@echo 'Git + Python 3.10+; Make is optional. Use python3 -B scripts/verify.py or the relevant Python helper directly.'
	@echo 'Host CLI only for automatic local install. After edits/branch switches: install-local, then a new host session.'
	@echo 'local-marketplace.example.json is optional. Runtime reads ignored .local/marketplace.json only.'
	@echo 'make sync-marketplace / check-marketplace: shared host catalogs'
	@echo 'make verify SOURCE=path  Read-only checks for the selected repository type'
	@echo 'make sync-plugin / check-plugin: generate or check marketplace and plugin metadata'
	@echo 'make test / verify / validate-docs'
	@echo 'make install-local TARGET=claude|codex DRY_RUN=0|1'
sync-plugin:
	$(MAKE) -C $(PLUGIN_DIR) sync-plugin
	$(PYTHON) scripts/marketplace.py sync
check-plugin:
	$(MAKE) -C $(PLUGIN_DIR) check-plugin
	$(PYTHON) scripts/marketplace.py check
# Test layers: deterministic checks by default; native/model tests are explicit.
TEST_GROUP ?=
.PHONY: test test-unit test-integration test-contracts test-native test-behavior
test test-unit test-integration test-contracts test-native:
	$(PYTHON) -B scripts/run_tests.py --kind $(if $(filter test,$@),deterministic,$(patsubst test-%,%,$@)) $(if $(TEST_GROUP),--group "$(TEST_GROUP)",)
	$(MAKE) -C $(PLUGIN_DIR) $@
test-behavior:
	$(MAKE) -C $(PLUGIN_DIR) test-behavior
verify:
	$(PYTHON) scripts/verify.py --source "$(SOURCE)" --kind auto $(if $(filter 1,$(REVIEW)),--review,)
validate-docs:
	$(MAKE) -C $(PLUGIN_DIR) validate-docs OUTPUT=.
install-local:
	$(PYTHON) scripts/local_plugins.py $@ --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)

.PHONY: sync-marketplace check-marketplace
sync-marketplace:
	$(PYTHON) scripts/marketplace.py sync
check-marketplace:
	$(PYTHON) scripts/marketplace.py check
