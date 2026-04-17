"""CapATL model checking: capacity constraints, error cases."""

import pytest

from model_checker.algorithms.explicit.CapATL.CapATL import (
    _core_capatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result


@pytest.mark.unit
@pytest.mark.model_checking
class TestCapATLErrorHandling:
    """Test CapATL error handling for invalid inputs."""

    def test_capatl_invalid_formula_syntax(self, capatl_model):
        """Test CapATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", capatl_model.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_capatl_nonexistent_atomic_proposition(self, capatl_model):
        """Test CapATL with non-existent atomic proposition."""
        result = _core_capatl_checking(capatl_model, "<{1,2},5>F nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()

    def test_capatl_invalid_coalition(self, capatl_model):
        """Test CapATL with invalid coalition (agent number out of range)."""
        result = _core_capatl_checking(capatl_model, "<{99},5>F p")
        assert "error" in result

    def test_capatl_negative_capacity(self, capatl_model):
        """Test CapATL with negative capacity (should be invalid)."""
        result = _core_capatl_checking(capatl_model, "<{1,2},-5>F p")
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_capatl_missing_capacity_value(self, capatl_model):
        """Test CapATL with missing capacity value."""
        result = _core_capatl_checking(capatl_model, "<{1,2}>F p")
        assert "error" in result or "Syntax error" in result.get("res", "")


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestCapATLSemantics:
    """Result format and winning states for CapATL."""

    def test_capatl_result_has_initial_state_and_winning_states(self, capatl_model):
        """Result includes initial_state key and res with winning state set."""
        result = _core_capatl_checking(capatl_model, "<{1},5>F g")
        assert "error" not in result
        assert "res" in result
        assert "initial_state" in result
        states = extract_states_from_result(result)
        assert states is not None
        assert len(states) >= 1, "At least one winning state expected for <{1},5>F g"
        assert "q2" in states, "q2 is a winning state for F g on this model"
