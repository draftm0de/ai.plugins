# Managed by the plugin manager: do not edit. Own targets and variables belong into CUSTOM.mk.
export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
SOURCE ?= .
TEST_GROUP ?=
TARGET ?= claude
DRY_RUN ?= 0
.SUFFIXES:
.DEFAULT_GOAL := help
.PHONY: help sync check test verify install-local
help:
	@echo 'sync / check          Generate / validate the host catalogs from marketplace.json'
	@echo 'test                  Deterministic tests; TEST_GROUP=<name> selects a component'
	@echo 'verify                Read-only structure checks; REVIEW=1 adds the scope review'
	@echo 'install-local         Install the local plugin checkouts, TARGET=claude|codex, DRY_RUN=1; then a new host session'
sync:
	$(PYTHON) scripts/marketplace.py sync
check:
	$(PYTHON) scripts/marketplace.py check
test:
	$(PYTHON) -B scripts/run_tests.py --kind deterministic $(if $(TEST_GROUP),--group "$(TEST_GROUP)",)
verify:
	$(PYTHON) scripts/verify/structure.py --source "$(SOURCE)"
	$(PYTHON) scripts/verify/standards.py --source "$(SOURCE)"
	$(PYTHON) scripts/verify/docs.py --source "$(SOURCE)"
	$(if $(filter 1,$(REVIEW)),$(PYTHON) scripts/verify/scope.py --source "$(SOURCE)",)
install-local:
	$(PYTHON) scripts/local_plugins.py install-local --target "$(TARGET)" $(if $(filter 1,$(DRY_RUN)),--dry-run,)

# Own targets of this repository; optional.
-include CUSTOM.mk
