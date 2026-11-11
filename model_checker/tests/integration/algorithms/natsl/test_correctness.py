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


@pytest.mark.integration
@pytest.mark.parametrize(
    ("constant", "expected"),
    [
        ("true", True),  # true holds in every state, so F true holds at once
        ("false", False),  # no state satisfies false, so F false never holds
    ],
)
def test_goal_constant_is_evaluated_like_in_every_other_logic(
    natatl_standard_model, constant, expected
):
    """`F true` is the constant, as in CTL and ATL, not an unknown proposition."""
    result = model_checking(
        f"E{{1}}x: (x, 1) F {constant}", natatl_standard_model.filename
    )
    assert "error" not in result, result
    assert result["Satisfiability"] is expected


@pytest.mark.integration
@pytest.mark.parametrize("name", ["or", "Next", "True", "_a"])
def test_goal_name_outside_the_proposition_alphabet_is_an_error(
    natatl_standard_model, name
):
    """The checker applies the shared proposition rule to the goal, not only the factory parser."""
    result = model_checking(f"E{{1}}x: (x, 1) F {name}", natatl_standard_model.filename)
    assert result["error"]["type"] == "validation", result
    assert f"Atomic proposition {name!r}" in result["error"]["message"], result
