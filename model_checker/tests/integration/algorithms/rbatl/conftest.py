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
def rover_model(test_data_dir):
    """Mars rover mission model from the original VITAMIN examples."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_2agents_11states_rover.txt"
    )
