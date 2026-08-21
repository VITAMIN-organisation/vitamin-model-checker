"""LTL model checking: linear path properties and Nash equilibrium APIs."""

import pytest

from model_checker.algorithms.explicit.LTL.LTL import (
    model_checking,
    model_checking_exists_nash,
)
from model_checker.tests.helpers.model_helpers import generate_linear_chain


@pytest.mark.unit
@pytest.mark.model_checking
class TestLTLErrorHandling:
    """Test LTL error handling for invalid inputs."""

    def test_ltl_invalid_formula_syntax(self, cgs_simple_parser):
        """Test LTL with invalid formula syntax."""
        result = model_checking("F p &", cgs_simple_parser.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_ltl_nonexistent_atomic_proposition(self, cgs_simple_parser):
        """Test LTL with non-existent atomic proposition."""
        result = model_checking("F nonexistent", cgs_simple_parser.filename)
        assert "error" in result or "does not exist" in result.get("res", "").lower()


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestLTLSemantics:
    """LTL sure-win oracles: Result {satisfied}/{} and initial-state truth."""

    @pytest.mark.parametrize(
        "formula,expected_res,expected_initial",
        [
            ("F q", "{satisfied}", True),
            ("F p", "{satisfied}", True),
            ("G p", "{}", False),
            ("X q", "{satisfied}", True),
            ("p U q", "{satisfied}", True),
        ],
    )
    def test_ltl_semantics_ctl_fixture(
        self, ctl_small_model, formula, expected_res, expected_initial
    ):
        """Pinned LTL bridge results on ctl_1agent_4states."""
        result = model_checking(formula, ctl_small_model.filename)
        assert "error" not in result
        assert result["res"] == f"Result: {expected_res}"
        suffix = "True" if expected_initial else "False"
        assert result["initial_state"].strip().endswith(suffix)

    def test_ltl_semantics_linear_chain(self, temp_file):
        """3-state chain s0->s1->s2; p at s0,s2; q at s2."""
        content = generate_linear_chain(
            3, num_agents=2, prop_names=["p", "q"], action_label="AC"
        )
        path = temp_file(content)

        cases = [
            ("F p", "{satisfied}", True),
            ("F q", "{satisfied}", True),
            ("G q", "{}", False),
            ("X q", "{}", False),
            ("p U q", "{}", False),
        ]
        for formula, expected_res, expected_initial in cases:
            result = model_checking(formula, path)
            assert "error" not in result, result
            assert result["res"] == f"Result: {expected_res}"
            suffix = "True" if expected_initial else "False"
            assert result["initial_state"].strip().endswith(suffix)

    def test_ltl_eventually_goal_on_minimal_model(self, ltl_minimal_model):
        """F goal is sure-win on the minimal LTL fixture."""
        result = model_checking("F goal", ltl_minimal_model.filename)
        assert "error" not in result
        assert result["res"] == "Result: {satisfied}"
        assert result["initial_state"].strip().endswith("True")

    def test_ltl_counterexample_globally_false_on_minimal(self, ltl_minimal_model):
        """G goal fails on the minimal LTL fixture."""
        result = model_checking("G goal", ltl_minimal_model.filename)
        assert "error" not in result
        assert result["res"] == "Result: {}"
        assert result["initial_state"].strip().endswith("False")


@pytest.mark.integration
@pytest.mark.model_checking
class TestLTLNashFunctions:
    """LTL Nash equilibrium API (exists_nash) with pinned Satisfiability."""

    def test_model_checking_exists_nash_f_q_is_satisfiable(self, ctl_small_model):
        """exists_nash for F q on the CTL fixture is satisfiable within bound 2."""
        result = model_checking_exists_nash(
            ctl_small_model.filename,
            "F q",
            k=2,
            agents=[1],
        )
        assert isinstance(result, dict)
        assert result.get("Satisfiability") is True
        assert 1 <= result["Complexity Bound"] <= 2
