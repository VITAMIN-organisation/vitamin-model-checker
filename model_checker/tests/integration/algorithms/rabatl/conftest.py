"""RABATL integration test fixtures."""

import pytest


@pytest.fixture
def rabatl_model(test_data_dir):
    """Load RABATL costCGS model (rabatl_3agents_medium_6states_costs.txt)."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/RABATL/rabatl_3agents_medium_6states_costs.txt"
    )
