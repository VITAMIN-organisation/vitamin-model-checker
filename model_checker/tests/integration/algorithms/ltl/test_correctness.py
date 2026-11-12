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
        assert "error" in result
        assert result["error"]["type"] == "syntax"

    def test_ltl_nonexistent_atomic_proposition(self, cgs_simple_parser):
        """Test LTL with non-existent atomic proposition."""
        result = model_checking("F nonexistent", cgs_simple_parser.filename)
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_ltl_uppercase_constant_is_a_syntax_error(self, ctl_small_model):
        """`TRUE` is a reserved word, not an undeclared name."""
        result = model_checking("F TRUE", ctl_small_model.filename)
        assert result["error"]["type"] == "syntax"

    @pytest.mark.parametrize(
        "formula,name",
        [
            ("F gOAL", "gOAL"),
            ("G p1", "p1"),
            ("p U my_prop", "my_prop"),
            ("F pUq", "pUq"),
        ],
    )
    def test_ltl_undeclared_name_is_an_error_naming_it(
        self, ctl_small_model, formula, name
    ):
        """Names with capitals, digits, `_` or a glued operator are checked like `p`."""
        result = model_checking(formula, ctl_small_model.filename)
        assert result["error"]["type"] == "semantic"
        assert f"{name!r} not among the model's declared propositions" in (
            result["error"]["message"]
        )


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestLTLSemantics:
    """LTL sure-win verdicts: `res` and the initial-state line both read True or False."""

    @staticmethod
    def _assert_verdict(result, holds):
        assert "error" not in result, result
        assert result["res"] == f"Result: {holds}"
        assert result["initial_state"] == f"Initial state s0: {holds}"

    @pytest.mark.parametrize(
        ("formula", "holds"),
        [("F q", True), ("F p", True), ("G p", False), ("X q", True), ("p U q", True)],
    )
    def test_ltl_semantics_ctl_fixture(self, ctl_small_model, formula, holds):
        """Verdicts on ctl_1agent_4states."""
        self._assert_verdict(model_checking(formula, ctl_small_model.filename), holds)

    @pytest.mark.parametrize(
        ("formula", "holds"),
        [
            ("F p", True),
            ("F q", True),
            ("G q", False),
            ("X q", False),
            ("p U q", False),
        ],
    )
    def test_ltl_semantics_linear_chain(self, temp_file, formula, holds):
        """Chain s0 -> s1 -> s2 with p at s0 and s2, q at s2: X q fails at s0 because s1 lacks q."""
        path = temp_file(
            generate_linear_chain(
                3, num_agents=2, prop_names=["p", "q"], action_label="AC"
            )
        )
        self._assert_verdict(model_checking(formula, path), holds)

    @pytest.mark.parametrize(
        ("formula", "holds"), [("F goal", True), ("G goal", False)]
    )
    def test_ltl_on_the_minimal_fixture(self, ltl_minimal_model, formula, holds):
        """goal is reached on ltl_1agent_3states_minimal but does not hold everywhere."""
        self._assert_verdict(model_checking(formula, ltl_minimal_model.filename), holds)


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
