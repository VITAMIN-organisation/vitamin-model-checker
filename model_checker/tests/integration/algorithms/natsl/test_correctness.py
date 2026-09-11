"""NatSL model checking: strategy specifications with sat/unsat pins."""

import pytest

from model_checker.algorithms.explicit.NatSL.core import model_checking


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatSLErrorHandling:
    """Test NatSL error handling for invalid inputs."""

    def test_natsl_invalid_syntax_returns_error(self, natatl_standard_model):
        result = model_checking("INVALID_SYNTAX", natatl_standard_model.filename)
        assert "error" in result

    def test_natsl_empty_formula_returns_error(self, natatl_standard_model):
        result = model_checking("", natatl_standard_model.filename)
        assert "error" in result


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatSLCorrectness:
    """NatSL sat and unsat pins on the standard NatATL fixture."""

    def test_natsl_known_satisfiable_formula(self, natatl_standard_model):
        """E{1}x:(x,1)F a is satisfiable (proposition a reachable)."""
        result = model_checking("E{1}x:(x,1)F a", natatl_standard_model.filename)
        assert "error" not in result, result
        assert result["Satisfiability"] is True
        assert result["res"] == "Result: True"
        assert result["initial_state"].endswith("True")

    def test_natsl_unsatisfiable_not_eventually(self, natatl_standard_model):
        """E{1}x:(x,1)!F a is unsatisfiable when a is reachable under bound 1."""
        result = model_checking("E{1}x:(x,1)!F a", natatl_standard_model.filename)
        assert "error" not in result, result
        assert result["Satisfiability"] is False
        assert result["res"] == "Result: False"
        assert result["initial_state"].endswith("False")

    def test_natsl_space_mode_existential_only_formula(self, natatl_standard_model):
        """Space schedule: existential-only F a is satisfiable."""
        result = model_checking(
            "E{1}x:(x,1)F a",
            natatl_standard_model.filename,
            mode="space",
        )
        assert "error" not in result, result
        assert result["Satisfiability"] is True
        assert result["Mode"] == "space-efficient"
