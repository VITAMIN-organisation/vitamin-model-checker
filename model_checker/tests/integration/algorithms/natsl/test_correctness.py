"""NatSL model checking: strategy specifications with sat/unsat pins."""

import pytest

from model_checker.algorithms.explicit.NatSL.Alternated.natSL import (
    model_checking as model_checking_alternated,
)
from model_checker.algorithms.explicit.NatSL.Sequential.natSL import (
    model_checking,
)


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

    def test_natsl_unsatisfiable_not_eventually(self, natatl_standard_model):
        """E{1}x:(x,1)!F a is unsatisfiable when a is reachable under bound 1."""
        result = model_checking("E{1}x:(x,1)!F a", natatl_standard_model.filename)
        assert "error" not in result, result
        assert result["Satisfiability"] is False

    def test_natsl_alternated_existential_only_formula(self, natatl_standard_model):
        """Alternated semantics: existential-only F a is satisfiable."""
        result = model_checking_alternated(
            "E{1}x:(x,1)F a", natatl_standard_model.filename
        )
        assert "error" not in result, result
        assert result["Satisfiability"] is True
