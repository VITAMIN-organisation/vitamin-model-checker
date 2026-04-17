"""Pytest config and shared fixtures for model checker tests."""

from pathlib import Path

import pytest


# Register custom markers to avoid warnings
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions/methods"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests for multiple components working together",
    )
    config.addinivalue_line(
        "markers",
        "semantic: Semantic verification tests that check correctness against formal definitions",
    )
    config.addinivalue_line("markers", "parser: Tests for parsing functionality")
    config.addinivalue_line("markers", "validation: Tests for validation logic")
    config.addinivalue_line(
        "markers", "model_checking: Tests for model checking algorithms"
    )
    config.addinivalue_line(
        "markers", "edge_case: Tests for edge cases and error conditions"
    )
    config.addinivalue_line(
        "markers", "robustness: Tests for robustness and error handling"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance tests for large state spaces and scalability",
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests for full user workflows")
    config.addinivalue_line(
        "markers", "workflow: Workflow tests (load model, run checker, extract result)"
    )


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory.

    All model and test data live under tests/fixtures/.
    Structure: fixtures/{CGS,costCGS,capCGS}/{LOGIC}/, fixtures/tests/{invalid,edge_cases}/.
    """
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file and return its path."""

    def _create_temp_file(content):
        temp_file = tmp_path / "temp_model.txt"
        temp_file.write_text(content)
        return str(temp_file)

    return _create_temp_file


def _load_fixture(test_data_dir, model_path: str):
    """Load a model from fixtures; used by model fixtures below."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(test_data_dir, model_path)


@pytest.fixture
def cgs_simple_parser(test_data_dir):
    """Load atl_2agents_4states_simple.txt (CGS/ATL). Most commonly used test model."""
    return _load_fixture(test_data_dir, "CGS/ATL/atl_2agents_4states_simple.txt")


@pytest.fixture
def ctl_small_model(test_data_dir):
    """Load ctl_1agent_4states.txt (CGS/CTL). Used by CTL and LTL tests."""
    return _load_fixture(test_data_dir, "CGS/CTL/ctl_1agent_4states.txt")


@pytest.fixture
def natatl_standard_model(test_data_dir):
    """Load natatl_1agent_4states_standard.txt (CGS/NATATL). Used by NatATL and NatSL tests."""
    return _load_fixture(test_data_dir, "CGS/NATATL/natatl_1agent_4states_standard.txt")


@pytest.fixture
def cost_ol_model(test_data_dir):
    """Load ol_2agents_medium_6states_costs.txt (costCGS/OL). Used by OL and parser structure tests."""
    return _load_fixture(
        test_data_dir, "costCGS/OL/ol_2agents_medium_6states_costs.txt"
    )


@pytest.fixture
def ltl_minimal_model(test_data_dir):
    """Load ltl_1agent_3states_minimal.txt (CGS/LTL). Used by e2e workflows."""
    return _load_fixture(test_data_dir, "CGS/LTL/ltl_1agent_3states_minimal.txt")


@pytest.fixture
def atl_strategy_model(test_data_dir):
    """Load atl_2agents_4states_strategy.txt (CGS/ATL). Used by e2e strategy workflow."""
    return _load_fixture(test_data_dir, "CGS/ATL/atl_2agents_4states_strategy.txt")


@pytest.fixture
def capatl_model(test_data_dir):
    """Load capatl_3agents_3states_example.txt (capCGS/CAPATL). Used by CapATL tests."""
    return _load_fixture(
        test_data_dir, "capCGS/CAPATL/capatl_3agents_3states_example.txt"
    )


@pytest.fixture
def atl_large_model(test_data_dir):
    """Load atl_tianji_game_full_2agents_49states.txt (CGS/ATL). Used by e2e performance workflow."""
    return _load_fixture(
        test_data_dir, "CGS/ATL/atl_tianji_game_full_2agents_49states.txt"
    )
