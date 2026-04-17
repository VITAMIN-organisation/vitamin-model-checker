"""OATL integration test fixtures."""

import pytest


@pytest.fixture
def oatl_model(test_data_dir):
    """Load OATL costCGS model (oatl_3agents_medium_6states_costs.txt)."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    return load_test_model(
        test_data_dir, "costCGS/OATL/oatl_3agents_medium_6states_costs.txt"
    )
