"""NatSL model checking: strategy specifications, error cases."""

import pytest

from model_checker.algorithms.explicit.NatSL.Sequential.natSL import (
    model_checking,
)


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatSLErrorHandling:
    """Test NatSL error handling for invalid inputs."""

    @pytest.mark.parametrize(
        "formula,expected_satisfiability",
        [
            ("", None),
            ("INVALID_SYNTAX", False),
        ],
    )
    def test_natsl_error_handling(
        self, natatl_standard_model, formula, expected_satisfiability
    ):
        """Test NatSL error handling for invalid inputs."""
        result = model_checking(formula, natatl_standard_model.filename)
        assert (
            "error" in result or result.get("Satisfiability") == expected_satisfiability
        )


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatSLCorrectness:
    """Test NatSL model checking with representative models."""

    def test_natsl_basic_formula(self, natatl_standard_model):
        """Test NatSL with valid NatSL formula (E{1}x:(x,1)F a)."""
        result = model_checking("E{1}x:(x,1)F a", natatl_standard_model.filename)
        if "error" not in result:
            assert "Satisfiability" in result
            assert isinstance(result["Satisfiability"], bool)

    def test_natsl_known_satisfiable_formula(self, natatl_standard_model):
        """E{1}x:(x,1)F a on the standard model is satisfiable (proposition a reachable)."""
        result = model_checking("E{1}x:(x,1)F a", natatl_standard_model.filename)
        assert (
            "error" not in result
        ), f"NatSL should not error on valid formula: {result}"
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result["Satisfiability"] is True
