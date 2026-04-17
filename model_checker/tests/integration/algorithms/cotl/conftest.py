"""COTL integration test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def cotl_model_path(test_data_dir):
    """Path to the COTL example model (shared by test_correctness and test_semantics)."""
    return Path(test_data_dir) / "costCGS" / "COTL" / "cotl_model.txt"


@pytest.fixture
def cotl_model(test_data_dir):
    """Load COTL costCGS model (cotl_model.txt). Use when a parser is needed."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(test_data_dir, "costCGS/COTL/cotl_model.txt")
