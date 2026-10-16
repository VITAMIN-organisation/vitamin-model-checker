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
        result = model_checking("<{1},1>F (", natatl_standard_model.filename)
        assert "error" in result
        assert result["error"]["type"] == "syntax"

    def test_natatl_nonexistent_atomic_proposition(self, natatl_standard_model):
        """Unknown atoms must not be reported as ordinary unsatisfiability."""
        result = model_checking("<{1}, 1>F nonexistent", natatl_standard_model.filename)
        assert "error" in result
        assert result["error"]["type"] == "semantic"


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLCorrectness:
    """Test NatATL model checking with representative models and formulas."""

    def test_legacy_standard_fixture_is_nondeterministic(self, natatl_standard_model):
        """Keep the original fixture: C has two different destinations at s0."""
        result = model_checking("<{1},1>Fa", natatl_standard_model.filename)
        assert result["error"]["type"] == "model"
        assert "Nondeterministic" in result["error"]["message"]
