SHELL := /usr/bin/env bash

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PY := $(BIN)/python
SANITYCTL := $(BIN)/sanityctl
PYINSTALLER := $(BIN)/pyinstaller

APP_NAME := sanityctl
MAIN_FILE := main.py
DIST_DIR := dist
BUILD_DIR := build
SPEC_FILE := $(APP_NAME).spec
BIN_PATH := $(DIST_DIR)/$(APP_NAME)

.DEFAULT_GOAL := help

.PHONY: help venv install reinstall ensure-build-tools build rebuild run-bin \
        example example-pass example-fail inline test clean distclean

help:
	@echo "Targets:"
	@echo "  make install      - create local .venv and install project"
	@echo "  make reinstall    - recreate .venv from scratch"
	@echo "  make build        - build standalone binary into dist/"
	@echo "  make rebuild      - clean build artifacts and rebuild binary"
	@echo "  make run-bin      - run the built binary with --help"
	@echo "  make example      - run examples/checks.yaml (current example set, may fail)"
	@echo "  make example-pass - run a passing inline example"
	@echo "  make example-fail - run a failing inline example"
	@echo "  make inline       - run a simple inline check"
	@echo "  make test         - run smoke tests"
	@echo "  make clean        - remove caches and build artifacts"
	@echo "  make distclean    - remove .venv and caches"

$(SANITYCTL):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"

venv: $(SANITYCTL)

install: $(SANITYCTL)

reinstall:
	rm -rf $(VENV)
	$(MAKE) install

$(MAIN_FILE):
	printf 'from sanityctl.cli import main\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n' > $(MAIN_FILE)

ensure-build-tools: $(SANITYCTL)
	@if [ ! -x "$(PYINSTALLER)" ]; then \
		$(PIP) install -e ".[build]"; \
	fi

build: ensure-build-tools $(MAIN_FILE)
	$(PYINSTALLER) \
		--onefile \
		--name $(APP_NAME) \
		--paths src \
		--collect-all yaml \
		--collect-all rich_argparse \
		$(MAIN_FILE)
	@echo
	@echo "Built binary: $(BIN_PATH)"

rebuild:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(SPEC_FILE)
	$(MAKE) build

run-bin: build
	./$(BIN_PATH) --help

example: $(SANITYCTL)
	$(SANITYCTL) run -f examples/checks.yaml --summary table

example-pass: $(SANITYCTL)
	$(SANITYCTL) run \
		--name "passing example" \
		--cmd "printf 'hello'" \
		--stdout-contains hell \
		--summary table

example-fail: $(SANITYCTL)
	$(SANITYCTL) run \
		--name "failing example" \
		--cmd "python -c 'import sys; sys.exit(7)'" \
		--expect-code 0 \
		--summary table

inline: $(SANITYCTL)
	$(SANITYCTL) run --name "hello" --cmd "printf 'hello'" --stdout-contains hell --summary

test: $(SANITYCTL)
	PYTHONPATH=src $(PY) -m pytest -q tests/test_smoke.py

clean:
	rm -rf .pytest_cache $(BUILD_DIR) $(DIST_DIR) $(SPEC_FILE)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

distclean: clean
	rm -rf $(VENV)
