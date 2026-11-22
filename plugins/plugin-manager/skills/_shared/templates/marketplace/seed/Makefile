export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
.SUFFIXES:
.PHONY: help install-local test
help:
	@echo 'install-local TARGET=claude|codex DRY_RUN=0|1: install all associated local plugins; then open a new host session'
	@echo 'test: deterministic tests (unit + integration + contracts)'
	@echo 'Everything else runs directly: python3 -B scripts/verify.py, scripts/marketplace.py sync|check'
install-local:
	$(PYTHON) scripts/local_plugins.py install-local --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)
test:
	$(PYTHON) -B scripts/run_tests.py --kind deterministic
