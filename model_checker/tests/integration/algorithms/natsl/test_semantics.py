"""NatSL on the fixture models in fixtures/CGS/NatSL, in both search modes.

"time" and "space" are two search orders and must agree on every verdict.
"""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.NatSL.core import model_checking

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "CGS" / "NatSL"
SHORTCUT_MODEL = _FIXTURES / "restricted_two_agent.txt"
OPPONENT_MODEL = _FIXTURES / "bounded_opponent.txt"
CONTROLLER_MODEL = _FIXTURES / "bounded_controller.txt"


def _both_modes(formula, model, expected):
    """Run in time and space mode; both give `expected` in every result field."""
    results = [model_checking(formula, model, mode=mode) for mode in ("time", "space")]
    for result in results:
        assert "error" not in result, result
        assert result["Satisfiability"] is expected
        assert result["res"] == f"Result: {expected}"
        assert str(result["initial_state"]).rstrip().endswith(str(expected))
    return results


@pytest.mark.integration
def test_unrestricted_opponent_is_decided_by_the_shortcut():
    """With bound 1 the opponent's strategies equal all its moves, so no enumeration is needed."""
    [time_result, _] = _both_modes(
        "E{1}x A{1}y: (x, 1)(y, 2) F goal", SHORTCUT_MODEL, True
    )
    assert time_result["Unrestricted-opponent shortcuts"] == 1


@pytest.mark.integration
def test_bounded_opponent_is_enumerated():
    """Here the opponent's bound-1 strategies are fewer than its moves, so each one is checked."""
    [time_result, _] = _both_modes(
        "E{1}x A{1}y: (x, 1)(y, 2) F goal", OPPONENT_MODEL, True
    )
    assert time_result["Unrestricted-opponent shortcuts"] == 0
    assert time_result["Universal profiles checked"] > 0


@pytest.mark.integration
def test_larger_opponent_bound_finds_a_counterstrategy():
    """Raising the opponent's bound to 2 gives it a strategy that blocks the goal."""
    _both_modes("E{1}x A{2}y: (x, 1)(y, 2) F goal", OPPONENT_MODEL, False)


@pytest.mark.integration
@pytest.mark.parametrize(("bound", "expected"), [(1, False), (2, True)])
def test_controller_needs_bound_two(bound, expected):
    """s0 needs A (B loops) and s1 needs B (A loops): one rule plays one action everywhere, so bound 1 fails."""
    results = _both_modes(f"E{{{bound}}}x: (x, 1) F goal", CONTROLLER_MODEL, expected)
    if expected:
        assert len(results[0]["Decisive assignment"]["x"]) == 2


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "model", "message"),
    [
        ("A{1}x E{1}y: (x, 1)(y, 2) F goal", SHORTCUT_MODEL, "E* A*"),
        ("E{1}x: (x, 1) F missing", CONTROLLER_MODEL, "Unknown proposition"),
    ],
    ids=["universal_before_existential", "undeclared_goal"],
)
def test_formula_outside_the_supported_fragment_is_an_error(formula, model, message):
    """The solver handles E* A* prefixes over declared propositions only."""
    result = model_checking(formula, model, mode="space")
    assert message in result["error"]["message"]


@pytest.mark.integration
def test_model_with_missing_joint_actions_is_an_error(temp_file):
    """s0 lists AA, AB and BA but not BB, so the opponent's reply table is not total."""
    model = temp_file(
        "Transition\nAA AB BA 0\n0 AA,AB,BA,BB 0 0\n0 0 AA,AB,BA,BB 0\n0 0 0 AA,AB,BA,BB\n"
        "Name_State\ns0 s1 s2 s3\nInitial_State\ns0\nAtomic_propositions\ngoal\n"
        "Labelling\n0\n1\n0\n0\nNumber_of_agents\n2\n"
    )
    result = model_checking("E{1}x A{1}y: (x, 1)(y, 2) F goal", model, mode="space")
    assert "Non-total local joint-action" in result["error"]["message"]
