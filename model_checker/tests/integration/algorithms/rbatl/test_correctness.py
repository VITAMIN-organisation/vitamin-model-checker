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
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_rbatl_nonexistent_atomic_proposition(self, rbatl_model):
        """Test RBATL with non-existent atomic proposition."""
        result = _core_rbatl_checking(rbatl_model, "<1><2>EF nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()

    def test_rbatl_invalid_coalition(self, rbatl_model):
        """Test RBATL with invalid coalition (agent number out of range)."""
        # Agent 99 doesn't exist in 3-agent model
        result = _core_rbatl_checking(rbatl_model, "<99><1>EF p")
        # Should error for invalid coalition
        assert "error" in result

    def test_rbatl_missing_dual_coalition(self, rbatl_model):
        """Test RBATL with missing dual coalition (should require two coalitions)."""
        result = _core_rbatl_checking(rbatl_model, "<1>EF p")
        assert "error" in result or "Syntax error" in result.get("res", "")


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
        assert "True" not in init_str and ": True" not in init_str
