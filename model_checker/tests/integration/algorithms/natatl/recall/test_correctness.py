"""NatATL Recall model checking: correctness and error handling."""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.natatl_recall import (
    model_checking,
)


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLRecallErrorHandling:
    """Error handling for invalid inputs."""

    def test_recall_invalid_formula_syntax(self, natatl_standard_model):
        """Invalid formula syntax yields an error."""
        result = model_checking("INVALID_SYNTAX", natatl_standard_model.filename)
        assert "error" in result

    def test_recall_empty_formula(self, natatl_standard_model):
        """Empty formula yields an error."""
        result = model_checking("", natatl_standard_model.filename)
        assert "error" in result


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLRecallCorrectness:
    """Test NatATL Recall model checking."""

    @pytest.mark.parametrize(
        "formula,expected_satisfiability,check_strategy",
        [("<{1},1>Fa", True, True)],
    )
    def test_recall_model_checking(
        self, natatl_standard_model, formula, expected_satisfiability, check_strategy
    ):
        """Test Recall model checking with various formulas."""
        result = model_checking(formula, natatl_standard_model.filename)

        if expected_satisfiability is None:
            assert "error" in result
        else:
            assert "Satisfiability" in result
            assert isinstance(result["Satisfiability"], bool)
            assert result["Satisfiability"] == expected_satisfiability
            if check_strategy:
                assert "Winning Strategy per agent" in result
