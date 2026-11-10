"""Shared fixtures: the fixture folder, temp model files and the common models."""

from itertools import count
from pathlib import Path

import pytest

from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.fixture
def test_data_dir():
    """Root of tests/fixtures: {CGS,costCGS,capCGS,...}/<LOGIC>/ and tests/invalid/."""
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def temp_file(tmp_path):
    """Write model text to a fresh file and return its path; each call gets its own name."""
    numbers = count()

    def _create_temp_file(content):
        path = tmp_path / f"model_{next(numbers)}.txt"
        path.write_text(content)
        return str(path)

    return _create_temp_file


@pytest.fixture
def cgs_simple_parser(test_data_dir):
    """2 agents, 4 states; the default ATL and CTL model."""
    return load_test_model(test_data_dir, "CGS/ATL/atl_2agents_4states_simple.txt")


@pytest.fixture
def ctl_small_model(test_data_dir):
    """1 agent, 4 states; CTL and LTL tests."""
    return load_test_model(test_data_dir, "CGS/CTL/ctl_1agent_4states.txt")


@pytest.fixture
def natatl_standard_model(test_data_dir):
    """1 agent, 4 states with idle actions; NatATL and NatSL tests."""
    return load_test_model(
        test_data_dir, "CGS/NATATL/natatl_1agent_4states_standard.txt"
    )


@pytest.fixture
def cost_ol_model(test_data_dir):
    """2 agents, 6 states with action costs; OL tests."""
    return load_test_model(
        test_data_dir, "costCGS/OL/ol_2agents_medium_6states_costs.txt"
    )


@pytest.fixture
def ltl_minimal_model(test_data_dir):
    """1 agent, 3 states; LTL tests."""
    return load_test_model(test_data_dir, "CGS/LTL/ltl_1agent_3states_minimal.txt")


@pytest.fixture
def capatl_model(test_data_dir):
    """3 agents, 3 states with capacities; CapATL tests."""
    return load_test_model(
        test_data_dir, "capCGS/CAPATL/capatl_3agents_3states_example.txt"
    )


@pytest.fixture
def atl_large_model(test_data_dir):
    """Tianji game, 2 agents, 49 states; the largest ATL fixture."""
    return load_test_model(
        test_data_dir, "CGS/ATL/atl_tianji_game_full_2agents_49states.txt"
    )
