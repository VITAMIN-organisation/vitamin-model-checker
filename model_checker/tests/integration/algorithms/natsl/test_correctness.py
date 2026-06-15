"""NatSL model checking: strategy specifications, error cases."""

import pytest

from model_checker.algorithms.explicit.NatSL.Alternated.natSL import (
    model_checking as model_checking_alternated,
)
from model_checker.algorithms.explicit.NatSL.Sequential.natSL import (
    model_checking,
)
from model_checker.synthetic_models import (
    generate_capcgs_linear_chain_model,
    generate_natatl_linear_chain_model,
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

    def test_natsl_alternated_existential_only_formula(self, natatl_standard_model):
        """Alternated semantics must handle existential-only formulas without error."""
        result = model_checking_alternated(
            "E{1}x:(x,1)F a", natatl_standard_model.filename
        )
        assert (
            "error" not in result
        ), f"NatSL Alternated should not error on valid formula: {result}"
        assert result["Satisfiability"] is True

    def test_natsl_sequential_synthetic_natatl_chain(self, temp_file):
        """Existential-only NatSL on synthetic NatATL chain must not IndexError."""
        content = generate_natatl_linear_chain_model(
            num_states=4, num_agents=2, prop_names=["p"]
        )
        model_path = temp_file(content)
        result = model_checking("E{1}x:(x,1)F p", model_path)
        assert "error" not in result, result
        assert isinstance(result["Satisfiability"], bool)

    def test_natsl_alternated_synthetic_natatl_chain(self, temp_file):
        """Alternated NatSL on synthetic NatATL chain must not IndexError."""
        content = generate_natatl_linear_chain_model(
            num_states=4, num_agents=2, prop_names=["p"]
        )
        model_path = temp_file(content)
        result = model_checking_alternated("E{1}x:(x,1)F p", model_path)
        assert "error" not in result, result
        assert isinstance(result["Satisfiability"], bool)


@pytest.mark.integration
@pytest.mark.model_checking
class TestCapATLSyntheticModels:
    """CapATL on in-memory synthetic capCGS chains."""

    def test_capatl_synthetic_linear_chain(self, temp_file):
        """Synthetic capCGS generator must assign one capacity row per agent."""
        from model_checker.algorithms.explicit.CapATL.CapATL import (
            model_checking as capatl_check,
        )

        content = generate_capcgs_linear_chain_model(
            num_states=4, num_agents=2, prop_names=["p"]
        )
        model_path = temp_file(content)
        result = capatl_check("<{1}, 1>F p", model_path)
        assert "error" not in result, result
        assert "True" in result.get("initial_state", "")
