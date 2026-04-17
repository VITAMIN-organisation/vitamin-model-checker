"""NatATL and NatATLF memoryless: error cases and correctness."""

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestNatATLErrorHandling:
    """Test NatATL error handling for invalid inputs."""

    def test_natatl_invalid_formula_syntax(self, natatl_standard_model):
        """Test NatATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", natatl_standard_model.filename)
        assert "error" in result or "Satisfiability" not in result

    def test_natatl_nonexistent_atomic_proposition(self, natatl_standard_model):
        """Test NatATL with non-existent atomic proposition."""
        result = model_checking("<{1}, 1>F nonexistent", natatl_standard_model.filename)
        assert (
            "error" in result
            or result.get("Satisfiability") is False
            or "does not exist" in str(result).lower()
        )


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLCorrectness:
    """Test NatATL model checking with representative models and formulas."""

    def test_natatl_1agent_standard_reachability(self, natatl_standard_model):
        """Test NatATL with standard 1-agent model for reachability."""
        formula = "<{1},1>Fa"
        result = model_checking(formula, natatl_standard_model.filename)
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result["Satisfiability"] is True
        assert "Winning Strategy per agent" in result
