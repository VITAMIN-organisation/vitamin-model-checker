"""RABATL model checking: dual coalitions and error cases."""

import pytest

from model_checker.algorithms.explicit.RABATL.RABATL import (
    _core_rabatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result


@pytest.mark.unit
@pytest.mark.model_checking
class TestRABATLErrorHandling:
    """Test RABATL error handling for invalid inputs."""

    def test_rabatl_invalid_formula_syntax(self, rabatl_model):
        """Test RABATL with invalid formula syntax."""
        # A name starts with a lowercase letter, so this is not a proposition.
        result = model_checking("INVALID_FORMULA", rabatl_model.filename)
        assert "error" in result
        assert result["error"]["type"] == "syntax"

    def test_rabatl_nonexistent_atomic_proposition(self, rabatl_model):
        """Test RABATL with non-existent atomic proposition."""
        result = _core_rabatl_checking(rabatl_model, "<1><2>F nonexistent")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_rabatl_invalid_coalition(self, rabatl_model):
        """Test RABATL with invalid coalition (agent number out of range)."""
        result = _core_rabatl_checking(rabatl_model, "<99><1>F p")
        assert "error" in result

    def test_rabatl_missing_dual_coalition(self, rabatl_model):
        """Test RABATL with missing dual coalition."""
        result = _core_rabatl_checking(rabatl_model, "<1>F p")
        assert "error" in result
        assert result["error"]["type"] == "syntax"


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRABATLSemantics:
    """Exact state-set semantics on fixture model."""

    def test_rabatl_exact_state_set(self, rabatl_model):
        """<1><2>F r: in s0 and s2 the others can keep the state, where r is false."""
        result = _core_rabatl_checking(rabatl_model, "<1><2>F r")
        assert "error" not in result
        assert "res" in result
        states = extract_states_from_result(result)
        assert states == {"s1", "s3", "s4"}
        init_str = result.get("initial_state", "")
        assert ": False" in init_str


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRABATLResultSet:
    """`res` is the exact bounded state set, also when the initial state is False."""

    def test_split_cost_of_the_coalition_decides_each_loop(self, rabatl_model):
        """r holds at s1, s3, s4, whose loops cost agent 1 0, 1 and 2 per step. Staying
        forever adds up, so only the free loop at s1 fits bound 1."""
        result = model_checking("<1><1>G r", rabatl_model.filename)
        assert "error" not in result
        assert extract_states_from_result(result) == {"s1"}
        assert ": False" in result["initial_state"]
