export PYTHONDONTWRITEBYTECODE := 1
PYTHON ?= python3
TARGET ?= claude
DRY_RUN ?= 0
MARKETPLACE ?=
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
	@echo 'Tests: test (unit + integration + contracts), test-unit, test-integration, test-contracts, test-native, test-behavior'
	@echo 'Git + Python 3.10+; Make is optional. Use python3 -B scripts/verify.py or the relevant Python helper directly.'
	@echo 'Host CLI only for automatic local install. After edits/branch switches: install-local, then a new host session.'
	@echo 'local-marketplace.example.json is optional. Runtime reads ignored .local/marketplace.json only.'
	@echo 'make install-local TARGET=claude|codex  Test checkout edits without GitHub'
	@echo 'make sync-plugin / check-plugin     Generate / validate committed repository import metadata'
	@echo 'make verify SOURCE=...             Read-only structure audit; host acceptance remains separate'
	@echo 'make inspect SOURCE=/path/to/skill  Inspect source without executing it'
	@echo 'make scaffold SOURCE=... OUTPUT=... Create missing doc templates and copy the icon'
	@echo 'make validate-docs OUTPUT=...       Validate finished docs; scaffolds intentionally fail'
	@echo 'make test                          All deterministic skill/shared/integration tests'
	@echo 'make test TEST_GROUP=publish        Select a skill/component within deterministic layers'

# Test layers: deterministic checks by default; native/model tests are explicit.
TEST_GROUP ?=
.PHONY: test test-unit test-integration test-contracts test-native test-behavior
test test-unit test-integration test-contracts test-native:
	$(PYTHON) -B scripts/run_tests.py --kind $(if $(filter test,$@),deterministic,$(patsubst test-%,%,$@)) $(if $(TEST_GROUP),--group "$(TEST_GROUP)",)
CLI ?= codex
CASE ?=
BEHAVIOR_OUTPUT ?=
test-behavior:
	$(PYTHON) -B tests/behavior/run_review.py --cli "$(CLI)" $(if $(CASE),--case "$(CASE)",) $(if $(BEHAVIOR_OUTPUT),--output-dir "$(BEHAVIOR_OUTPUT)",)
inspect:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" >&2; exit 2)
	$(PYTHON) skills/_shared/scripts/documentation.py inspect --source "$(SOURCE)"
scaffold:
	@test -n "$(SOURCE)" -a -n "$(OUTPUT)" || (echo "SOURCE and OUTPUT are required" >&2; exit 2)
	$(PYTHON) skills/_shared/scripts/documentation.py scaffold --source "$(SOURCE)" --output "$(OUTPUT)" $(if $(TITLE),--title "$(TITLE)",) $(if $(LANGUAGES),--languages $(LANGUAGES),) $(if $(DEFAULT_LANGUAGE),--default-language $(DEFAULT_LANGUAGE),)
validate-docs:
	@test -n "$(OUTPUT)" || (echo "OUTPUT is required" >&2; exit 2)
	$(PYTHON) skills/_shared/scripts/documentation.py validate --output "$(OUTPUT)"

.PHONY: verify
verify:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" >&2; exit 2)
	$(PYTHON) skills/_shared/scripts/verify.py --source "$(SOURCE)" --kind auto $(if $(filter 1,$(REVIEW)),--review,)


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
