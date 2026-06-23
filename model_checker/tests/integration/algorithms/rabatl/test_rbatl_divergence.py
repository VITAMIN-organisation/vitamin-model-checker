"""RABATL vs RBATL semantics where coalition-sum costs differ from flat costs."""

import pytest

from model_checker.algorithms.explicit.RABATL.RABATL import _core_rabatl_checking
from model_checker.algorithms.explicit.RBATL.RBATL import _core_rbatl_checking
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_test_model,
)


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRABATLVsRBATLDivergence:
    """Same formula syntax, different cost models -> different winning sets."""

    @pytest.fixture
    def rabatl_fixture(self, test_data_dir):
        return load_test_model(
            test_data_dir, "costCGS/RABATL/rabatl_3agents_medium_6states_costs.txt"
        )

    @pytest.fixture
    def rbatl_fixture(self, test_data_dir):
        return load_test_model(
            test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )

    def test_split_matrix_coalition_sum_differs_from_flat_costs(
        self, rabatl_fixture, rbatl_fixture
    ):
        formula = "<1><1,1,1>F r"
        rab_states = extract_states_from_result(
            _core_rabatl_checking(rabatl_fixture, formula)
        )
        rba_states = extract_states_from_result(
            _core_rbatl_checking(rbatl_fixture, formula)
        )
        assert rab_states == {"s0", "s1", "s2", "s3"}
        assert rba_states == {"s0", "s2"}
        assert rab_states != rba_states

    def test_multi_agent_coalition_bound_vector_divergence(
        self, rabatl_fixture, rbatl_fixture
    ):
        formula = "<1,2><2,2,2>F r"
        rab_states = extract_states_from_result(
            _core_rabatl_checking(rabatl_fixture, formula)
        )
        rba_states = extract_states_from_result(
            _core_rbatl_checking(rbatl_fixture, formula)
        )
        assert rab_states == {"s0", "s1", "s2", "s3"}
        assert rba_states == {"s0", "s1", "s2", "s3", "s4"}
        assert rab_states != rba_states
