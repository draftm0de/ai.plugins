export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
PLUGIN_DIR := plugins/plugin-manager
.SUFFIXES:
.PHONY: help sync-plugin check-plugin test verify validate-docs check-docs-export export-docs install-local update-local
help:
	@echo 'make sync-plugin / check-plugin: generate or check marketplace and plugin metadata'
	@echo 'make test / verify / validate-docs / check-docs-export'
	@echo 'make install-local / update-local TARGET=claude|codex DRY_RUN=0|1'
sync-plugin:
	$(MAKE) -C $(PLUGIN_DIR) sync-plugin
	$(PYTHON) scripts/marketplace.py sync
check-plugin:
	$(MAKE) -C $(PLUGIN_DIR) check-plugin
	$(PYTHON) scripts/marketplace.py check
test:
	$(PYTHON) -m unittest discover -s tests -v
	$(MAKE) -C $(PLUGIN_DIR) test
verify:
	$(MAKE) -C $(PLUGIN_DIR) verify SOURCE=.
validate-docs:
	$(MAKE) -C $(PLUGIN_DIR) validate-docs OUTPUT=.
check-docs-export export-docs:
	$(MAKE) -C $(PLUGIN_DIR) $@
install-local update-local:
	$(MAKE) -C $(PLUGIN_DIR) $@ TARGET=$(TARGET) DRY_RUN=$(DRY_RUN)
