from pathlib import Path
import tempfile

import pytest

from model_checker.parsers.formulas.NatSL.parser import (
    UnsupportedTranslationError,
    convert_natsl_to_natatl,
    goal_to_ctl,
    parse_formula,
)
from model_checker.algorithms.explicit.NatSL.core import model_checking


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "fixtures" / "CGS" / "NatSL"

SHORTCUT_MODEL = FIXTURES / "restricted_two_agent.txt"
OPPONENT_MODEL = FIXTURES / "bounded_opponent.txt"
CONTROLLER_MODEL = FIXTURES / "bounded_controller.txt"


def both_modes(formula, model, expected):
    results = [
        model_checking(formula, model, mode=mode)
        for mode in ("time", "space")
    ]
    assert [result["Satisfiability"] for result in results] == [expected, expected]
    return results


def test_prefix_order_is_preserved():
    parsed = parse_formula("E{1}xA{2}y:(x,1)(y,2)Fgoal")
    assert [q.kind for q in parsed.quantifiers] == ["E", "A"]
    assert [q.bound for q in parsed.quantifiers] == [1, 2]


def test_mixed_translation_is_rejected():
    with pytest.raises(UnsupportedTranslationError):
        convert_natsl_to_natatl(
            "E{1}xA{1}y:(x,1)(y,2)Fgoal"
        )


def test_negated_global_uses_universal_path_semantics():
    goal = parse_formula("E{1}x:(x,1)!Ggoal").goal
    assert goal_to_ctl(goal) == "AF !goal"


def test_unrestricted_opponent_shortcut():
    results = both_modes(
        "E{1}xA{1}y:(x,1)(y,2)Fgoal",
        SHORTCUT_MODEL,
        True,
    )
    assert results[0]["Unrestricted-opponent shortcuts"] == 1


def test_bounded_opponent_requires_explicit_enumeration():
    results = both_modes(
        "E{1}xA{1}y:(x,1)(y,2)Fgoal",
        OPPONENT_MODEL,
        True,
    )
    assert results[0]["Unrestricted-opponent shortcuts"] == 0
    assert results[0]["Universal profiles checked"] > 0


def test_larger_universal_bound_exposes_counterstrategy():
    both_modes(
        "E{1}xA{2}y:(x,1)(y,2)Fgoal",
        OPPONENT_MODEL,
        False,
    )


def test_controller_bound_one_is_insufficient():
    both_modes(
        "E{1}x:(x,1)Fgoal",
        CONTROLLER_MODEL,
        False,
    )


def test_controller_bound_two_finds_conditional_strategy():
    results = both_modes(
        "E{2}x:(x,1)Fgoal",
        CONTROLLER_MODEL,
        True,
    )
    pairs = results[0]["Decisive assignment"]["x"]
    assert len(pairs) >= 2


def test_out_of_fragment_prefix_is_rejected():
    with pytest.raises(ValueError, match=r"E\* A\*"):
        model_checking(
            "A{1}xE{1}y:(x,1)(y,2)Fgoal",
            SHORTCUT_MODEL,
            mode="space",
        )


def test_unknown_proposition_is_rejected():
    with pytest.raises(ValueError, match="Unknown proposition"):
        model_checking(
            "E{1}x:(x,1)Fmissing",
            CONTROLLER_MODEL,
            mode="space",
        )


def test_non_total_local_joint_action_table_is_rejected():
    model = """Transition
AA AB BA 0
0 AA,AB,BA,BB 0 0
0 0 AA,AB,BA,BB 0
0 0 0 AA,AB,BA,BB
Unknown_Transition_by
0 0 0 0
0 0 0 0
0 0 0 0
0 0 0 0
Name_State
s0 s1 s2 s3
Initial_State
s0
Atomic_propositions
goal
Labelling
0
1
0
0
Number_of_agents
2
"""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "non_total.txt"
        path.write_text(model, encoding="utf-8")

        with pytest.raises(
            ValueError,
            match="Non-total local joint-action",
        ):
            model_checking(
                "E{1}xA{1}y:(x,1)(y,2)Fgoal",
                path,
                mode="space",
            )
