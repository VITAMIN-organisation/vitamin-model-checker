# Intended to be run from model_checker/ or project root.

.PHONY: help install build clean format lint typecheck test test-models release-check publish-test publish tag push-tag release

# Configuration
PYTHON := python3
# Command that uploads to PyPI; set UV="echo uv" to see the command without uploading.
UV ?= uv
# Directory containing this Makefile (model_checker)
MKFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
# Project root (local directory)
PROJECT_ROOT := $(MKFILE_DIR)

help:
	@echo "VITAMIN Model Checker"
	@echo ""
	@echo "  --- Setup ---"
	@echo "  make install       Install package in development mode"
	@echo ""
	@echo "  --- Build & Cleanup ---"
	@echo "  make build         Build distribution package"
	@echo "  make clean         Remove Python cache and egg-info"
	@echo ""
	@echo "  --- Release (version from pyproject.toml) ---"
	@echo "  make release-check Lint, typecheck, fast tests, build, twine check; uploads and tags nothing"
	@echo "  make publish-test  Upload dist/ to TestPyPI (asks you to type the version)"
	@echo "  make publish       Upload dist/ to PyPI (asks you to type the version)"
	@echo "  make tag           Create the local tag v<version>"
	@echo "  make push-tag      Push the tag to origin"
	@echo "  make release       release-check, publish, tag, push-tag in order"
	@echo ""
	@echo "  --- Quality ---"
	@echo "  make format        Format code with black"
	@echo "  make lint          Lint code with ruff"
	@echo "  make typecheck     Type-check model_checker/ with basedpyright"
	@echo "  make generate-parsers Generate parsing tables for all logics"
	@echo "  make test          Run unit and integration tests (fast)"

# Setup
install:
	@echo "Installing package..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -m pip install -e ".[dev]"
	@echo "Done."

# Build & Cleanup
build:
	@echo "Building distribution package..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -m pip install -q build wheel setuptools 2>/dev/null || true
	@cd $(PROJECT_ROOT) && $(PYTHON) -m build
	@echo "Done. Artifacts in $(PROJECT_ROOT)/dist/"

clean:
	@echo "Cleaning cache and egg-info..."
	@cd $(MKFILE_DIR) && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@cd $(MKFILE_DIR) && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@cd $(MKFILE_DIR) && find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@cd $(MKFILE_DIR) && find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Done."

generate-parsers:
	@echo "Generating parser tables for all logics..."
	@$(PYTHON) -c "import glob, importlib; \
	[getattr(importlib.import_module(f.replace('/', '.')[:-3]), attr)() \
	for f in glob.glob('model_checker/parsers/formulas/*/parser.py') \
	for attr in dir(importlib.import_module(f.replace('/', '.')[:-3])) \
	if attr.endswith('Parser') and attr != 'BaseLogicParser']"
	@echo "Done."

# Quality
format:
	@command -v black >/dev/null 2>&1 || { echo "Install black: $(PYTHON) -m pip install black"; exit 1; }
	@cd $(MKFILE_DIR) && black .

lint:
	@command -v ruff >/dev/null 2>&1 || { echo "Install ruff: $(PYTHON) -m pip install ruff"; exit 1; }
	@cd $(PROJECT_ROOT) && ruff check model_checker/

typecheck:
	@command -v basedpyright >/dev/null 2>&1 || { echo "Install basedpyright: $(PYTHON) -m pip install '.[dev]'"; exit 1; }
	@echo "Type-checking model_checker/ (baseline: .basedpyright/baseline.json)..."
	@cd $(PROJECT_ROOT) && basedpyright --level error
	@echo "Done."

test:
	@echo "Running unit and integration tests..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -m pytest model_checker/tests/
	@echo "Done."

# Release: the logic is in scripts/release.sh. Anything that uploads or tags asks for the version.
RELEASE := UV="$(UV)" PYTHON="$(PYTHON)" bash "$(PROJECT_ROOT)/scripts/release.sh"

release-check:
	@$(RELEASE) check

publish-test:
	@$(RELEASE) publish-test

publish:
	@$(RELEASE) publish

tag:
	@$(RELEASE) tag

push-tag:
	@$(RELEASE) push-tag

release:
	@$(MAKE) release-check
	@$(MAKE) publish
	@$(MAKE) tag
	@$(MAKE) push-tag
