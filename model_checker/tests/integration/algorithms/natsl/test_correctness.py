"""NatSL model checking: strategy specifications with sat/unsat pins."""

import pytest

from model_checker.algorithms.explicit.NatSL.core import model_checking


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatSLCorrectness:
    """NatSL sat and unsat pins on the standard NatATL fixture."""

    def test_natsl_known_satisfiable_formula(self, natatl_standard_model):
        """E{1}x: (x, 1) F a is satisfiable (proposition a reachable)."""
        result = model_checking("E{1}x: (x, 1) F a", natatl_standard_model.filename)
        assert "error" not in result, result
        assert result["Satisfiability"] is True
        assert result["res"] == "Result: True"
        assert result["initial_state"].endswith("True")

    def test_natsl_unsatisfiable_not_eventually(self, natatl_standard_model):
        """E{1}x: (x, 1) !F a is unsatisfiable when a is reachable under bound 1."""
        result = model_checking("E{1}x: (x, 1) !F a", natatl_standard_model.filename)
        assert "error" not in result, result
        assert result["Satisfiability"] is False
        assert result["res"] == "Result: False"
        assert result["initial_state"].endswith("False")
