"""RBATL model checking: dual coalitions, CTL-like operators, error cases."""

import pytest

from model_checker.algorithms.explicit.RBATL.RBATL import (
    _core_rbatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result


@pytest.mark.unit
@pytest.mark.model_checking
class TestRBATLErrorHandling:
    """Test RBATL error handling for invalid inputs."""

    def test_rbatl_invalid_formula_syntax(self, rbatl_model):
        """Test RBATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", rbatl_model.filename)
        assert "error" in result

    def test_rbatl_nonexistent_atomic_proposition(self, rbatl_model):
        """Test RBATL with non-existent atomic proposition."""
        result = _core_rbatl_checking(rbatl_model, "<1><2>F nonexistent")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_rbatl_invalid_coalition(self, rbatl_model):
        """Test RBATL with invalid coalition (agent number out of range)."""
        # Agent 99 doesn't exist in 3-agent model
        result = _core_rbatl_checking(rbatl_model, "<99><1>EF p")
        # Should error for invalid coalition
        assert "error" in result

    def test_rbatl_missing_dual_coalition(self, rbatl_model):
        """Test RBATL with missing dual coalition (should require two coalitions)."""
        result = _core_rbatl_checking(rbatl_model, "<1>EF p")
        assert "error" in result


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLSemantics:
    """Exact state-set semantics on fixture model."""

    def test_rbatl_exact_state_set(self, rbatl_model):
        """Model checker returns the expected state set for <1><2>F r."""
        result = _core_rbatl_checking(rbatl_model, "<1><2>F r")
        assert "error" not in result
        assert "res" in result
        states = extract_states_from_result(result)
        assert states == {"s0", "s1", "s2", "s3", "s4"}
        init_str = result.get("initial_state", "")
        assert ": True" in init_str

    def test_rbatl_true_false_constants(self, rbatl_model):
        """Boolean constants must resolve via the formula parser, not as atoms."""
        true_result = _core_rbatl_checking(rbatl_model, "<1><2>F true")
        assert "error" not in true_result, true_result
        assert extract_states_from_result(true_result) == {
            "s0",
            "s1",
            "s2",
            "s3",
            "s4",
            "s5",
        }

        false_result = _core_rbatl_checking(rbatl_model, "<1><2>F false")
        assert "error" not in false_result, false_result
        assert extract_states_from_result(false_result) == set()


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLResultSet:
    """`res` is the exact bounded state set, also when the initial state is False."""

    def test_bound_below_every_loop_cost_gives_empty_set(self, rbatl_model):
        """r holds at s1, s3, s4, whose only move is a loop of cost 2 (`*** s1$2:2`, `s3$2:2`, `s4$2:2`).

        With bound 1 no loop is affordable, so no state keeps G r and the set is empty.
        Plain ATL `<1>G r` would list s1, s3 and s4.
        """
        result = model_checking("<1><1>G r", rbatl_model.filename)
        assert "error" not in result
        assert extract_states_from_result(result) == set()
        assert ": False" in result["initial_state"]

    def test_invalid_bound_is_reported_when_atl_is_false(self, rbatl_model):
        """A bound above 1000000 is an error whatever plain ATL says."""
        result = model_checking("<1><1000001>G r", rbatl_model.filename)
        assert "Invalid bound value 1000001" in result["error"]["message"]


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLZeroBound:
    """Bound 0 keeps only the moves that cost 0."""

    @pytest.mark.parametrize(
        ("formula", "expected"),
        [("<1><0>F p", {"s2"}), ("<1><0>G q", {"s0", "s1"})],
    )
    def test_only_free_moves(self, chain_model, formula, expected):
        """Only the cost-0 self-loops are left, so s0 and s1 stay where they are."""
        result = model_checking(formula, chain_model.filename)
        assert extract_states_from_result(result) == expected

    def test_rover_mission_formula_runs(self, rover_model):
        """The rover paper's mission formula nests <1><0,0>; no repair fits (5,1)."""
        formula = (
            "<1,2><5,1>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))"
        )
        result = model_checking(formula, rover_model.filename)
        assert extract_states_from_result(result) == {"s4", "s5", "s6", "s7", "s8"}
