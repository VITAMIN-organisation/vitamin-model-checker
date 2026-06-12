# Intended to be run from model_checker/ or project root.

.PHONY: help install build clean format lint test test-models

# ------------------------------
# Configuration
# ------------------------------
PYTHON := python3
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
	@echo "  --- Quality ---"
	@echo "  make format        Format code with black"
	@echo "  make lint          Lint code with ruff"
	@echo "  make test          Run unit and integration tests (fast)"

# ------------------------------
# Setup
# ------------------------------
install:
	@echo "Installing package..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -m pip install -e ".[dev]"
	@echo "Done."

# ------------------------------
# Build & Cleanup
# ------------------------------
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

# ------------------------------
# Quality
# ------------------------------
format:
	@command -v black >/dev/null 2>&1 || { echo "Install black: $(PYTHON) -m pip install black"; exit 1; }
	@cd $(MKFILE_DIR) && black .

lint:
	@command -v ruff >/dev/null 2>&1 || { echo "Install ruff: $(PYTHON) -m pip install ruff"; exit 1; }
	@cd $(PROJECT_ROOT) && ruff check model_checker/

test:
	@echo "Running unit and integration tests..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -m pytest -m "not slow" model_checker/tests/
	@echo "Done."
