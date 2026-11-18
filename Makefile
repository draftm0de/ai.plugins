export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
SOURCE ?= .
PLUGIN_DIR := plugins/plugin-manager
.SUFFIXES:
.PHONY: plugin-verify marketplace-verify help sync-plugin check-plugin test verify validate-docs check-docs-export export-docs install-local update-local
help:
	@echo 'make plugin-verify / marketplace-verify SOURCE=path  Read-only checks for the selected repository type'
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
verify plugin-verify marketplace-verify:
	$(PYTHON) $(PLUGIN_DIR)/skills/plugin-manager/scripts/verify.py --source "$(SOURCE)" --kind $(if $(filter plugin-verify,$@),plugin,$(if $(filter marketplace-verify,$@),marketplace,auto))
validate-docs:
	$(MAKE) -C $(PLUGIN_DIR) validate-docs OUTPUT=.
check-docs-export export-docs:
	$(MAKE) -C $(PLUGIN_DIR) $@
install-local update-local:
	$(PYTHON) scripts/local_plugins.py $@ --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)
