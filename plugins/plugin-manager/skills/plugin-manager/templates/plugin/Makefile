include docs.mk
export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
.PHONY: help test
help:
	@echo 'make install-local / update-local TARGET=claude|codex  Test checkout edits without GitHub'
	@echo 'make sync-plugin / check-plugin     Generate / validate committed repository import metadata'
	@echo 'make check-docs-export / export-docs  Validate / build the website documentation bundle'
test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

# Local development and repository metadata
# Disable implicit shell-script rules (for example install.sh -> install).
.SUFFIXES:
.PHONY: install-local update-local check-plugin sync-plugin
install-local:
	$(PYTHON) scripts/plugin.py install-local --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)
update-local:
	$(PYTHON) scripts/plugin.py update-local --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)
check-plugin:
	$(PYTHON) scripts/plugin.py check
sync-plugin:
	$(PYTHON) scripts/plugin.py sync
# End plugin commands
