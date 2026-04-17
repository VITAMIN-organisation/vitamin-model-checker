"""RBATL integration test fixtures."""

import pytest


@pytest.fixture
def rbatl_model(test_data_dir):
    """Load RBATL costCGS model (rbatl_3agents_medium_6states_costs.txt)."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
    )
