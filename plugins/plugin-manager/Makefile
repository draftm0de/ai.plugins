include docs.mk
export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
SOURCE ?= .
OUTPUT ?=
LANGUAGES ?=
REPOSITORY ?=
PLUGIN_NAME ?=
AUTHOR ?=
DEFAULT_LANGUAGE ?=
TITLE ?=

.PHONY: help test inspect scaffold validate-docs
help:
	@echo 'make install-local / update-local TARGET=claude|codex  Test checkout edits without GitHub'
	@echo 'make sync-plugin / check-plugin     Generate / validate committed repository import metadata'
	@echo 'make check-docs-export / export-docs  Validate / build the website documentation bundle'
	@echo 'make verify SOURCE=...             Read-only structure audit; host acceptance remains separate'
	@echo 'make init-plugin SOURCE=... OUTPUT=...  Scaffold a separate empty plugin repository'
	@echo 'make inspect SOURCE=/path/to/skill  Inspect source without executing it'
	@echo 'make scaffold SOURCE=... OUTPUT=... Create missing doc templates and copy the icon'
	@echo 'make validate-docs OUTPUT=...       Validate finished docs; scaffolds intentionally fail'
	@echo 'make test                          Deterministic unit/integration tests'

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
inspect:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" >&2; exit 2)
	$(PYTHON) skills/plugin-manager/scripts/documentation.py inspect --source "$(SOURCE)"
scaffold:
	@test -n "$(SOURCE)" -a -n "$(OUTPUT)" || (echo "SOURCE and OUTPUT are required" >&2; exit 2)
	$(PYTHON) skills/plugin-manager/scripts/documentation.py scaffold --source "$(SOURCE)" --output "$(OUTPUT)" $(if $(TITLE),--title "$(TITLE)",) $(if $(LANGUAGES),--languages $(LANGUAGES),) $(if $(DEFAULT_LANGUAGE),--default-language $(DEFAULT_LANGUAGE),)
validate-docs:
	@test -n "$(OUTPUT)" || (echo "OUTPUT is required" >&2; exit 2)
	$(PYTHON) skills/plugin-manager/scripts/documentation.py validate --output "$(OUTPUT)"

.PHONY: verify init-plugin
verify:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" >&2; exit 2)
	$(PYTHON) skills/plugin-manager/scripts/verify.py --source "$(SOURCE)" --kind auto
init-plugin:
	@test -n "$(SOURCE)" -a -n "$(OUTPUT)" || (echo "SOURCE and OUTPUT are required" >&2; exit 2)
	$(PYTHON) skills/plugin-manager/scripts/plugin_audit.py init --source "$(SOURCE)" --output "$(OUTPUT)" $(if $(LANGUAGES),--languages $(LANGUAGES),) $(if $(DEFAULT_LANGUAGE),--default-language $(DEFAULT_LANGUAGE),) $(if $(REPOSITORY),--repository "$(REPOSITORY)",) $(if $(AUTHOR),--author "$(AUTHOR)",) $(if $(PLUGIN_NAME),--plugin-name "$(PLUGIN_NAME)",)

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
