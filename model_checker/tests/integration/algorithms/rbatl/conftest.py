"""RBATL integration test fixtures."""

import pytest


@pytest.fixture
def rbatl_model(test_data_dir):
    """Load RBATL costCGS model (rbatl_3agents_medium_6states_costs.txt)."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
    )


@pytest.fixture
def chain_model(test_data_dir):
    """One agent, s0 -> s1 -> s2; each forward step costs 1, each self-loop 0."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_1agent_3states_chain.txt"
    )


@pytest.fixture
def sensor_model(test_data_dir):
    """Two sensors reach s6 at (energy, memory) cost (3,1) at least, via s1 and s4."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_2agents_8states_sensor.txt"
    )


@pytest.fixture
def rover_model(test_data_dir):
    """Mars rover mission model from the original VITAMIN examples."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_2agents_11states_rover.txt"
    )


@pytest.fixture
def loop_model(test_data_dir):
    """Agent 1 cannot choose between staying at s and moving to t; t -> u costs 1."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_2agents_3states_loop.txt"
    )
