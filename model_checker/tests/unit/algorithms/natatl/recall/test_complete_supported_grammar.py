"""Semantic examples, not a mechanized completeness proof.

Run from the repository root:
    python -m pytest model_checker/tests/unit/algorithms/natatl/recall/test_complete_supported_grammar.py
Proof scope: docs/NatATL/RECALL_COMPLETENESS.md.
Independent AST/cost/language tests: test_independent_regex_oracle.py.
"""
import pytest

from model_checker.algorithms.explicit.NatATL.Recall.recall_compositional import (
    check_compositional_recall_ast,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_solver import (
    solve_bounded_recall,
)


class TwoAgentAdversarialCGS:
    """The goal is reachable but an opponent can prevent it forever."""
    states = ["s0", "goal", "trap"]
    initial_state = "s0"
    atomic_propositions = ["goal"]
    matrix_prop = [[0], [1], [0]]
    graph = [
        ["IDLE|BLOCK,IDLE|ALLOW", "MOVE|ALLOW", "MOVE|BLOCK"],
        [0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW", 0],
        [0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW"],
    ]
    def get_number_of_agents(self):
        return 2


class TwoAgentForcedGoalCGS:
    """Both opponent responses to IDLE lead to a goal after two steps."""
    states = ["s0", "left", "right", "goal", "trap"]
    initial_state = "s0"
    atomic_propositions = ["goal"]
    matrix_prop = [[0], [0], [0], [1], [0]]
    graph = [
        [0, "IDLE|BLOCK", "IDLE|ALLOW", 0, "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW", "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW", "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW", 0],
        [0, 0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW"],
    ]
    def get_number_of_agents(self):
        return 2




def complete(cgs, ast):
    return check_compositional_recall_ast(cgs, ast, generator="extended", complete_supported_grammar=True)


def test_exhaustive_negative_certificate():
    result = solve_bounded_recall(TwoAgentAdversarialCGS(), [1], 3, "F", {"goal"},
                                  generator="extended", certify_restricted_exhaustion=True)
    assert result["Satisfiability"] is False
    assert result["Negative Certificate"] == "EXHAUSTIVE_BOUNDED_RECALL_ENUMERATION"
    assert result["Candidates Examined"] > 1


def test_uncertified_exhaustion_stays_unknown():
    result = solve_bounded_recall(TwoAgentAdversarialCGS(), [1], 3, "F", {"goal"}, generator="extended")
    assert result["Satisfiability"] is None


def test_certified_negative_can_be_negated():
    result = complete(TwoAgentAdversarialCGS(), ("!", ("<{1},3>F", "goal")))
    assert result["Satisfiability"] is True
    assert result["Supported Grammar Complete"] is True


@pytest.mark.parametrize("modal,expected", [
    (("<{1},3>X", "goal"), False), (("<{1},3>G", "goal"), False),
    (("<{1},3>F", "goal"), False), (("<{1},3>U", "true", "goal"), False),
    (("<{1},3>W", "goal", "goal"), False), (("<{1},3>W", "true", "goal"), True),
])
def test_universal_temporal_oracles(modal, expected):
    assert complete(TwoAgentAdversarialCGS(), modal)["Satisfiability"] is expected


def test_cost_bound_is_not_path_depth():
    cgs = TwoAgentForcedGoalCGS()
    assert complete(cgs, ("<{1},1>F", "goal"))["Satisfiability"] is True
    assert complete(cgs, ("<{1},1>X", "goal"))["Satisfiability"] is False


def test_nested_modalities_have_the_expected_truth_value():
    outer = ("<{1},1>G", ("!", ("<{1},3>F", "goal")))
    result = complete(TwoAgentAdversarialCGS(), outer)
    assert result["Satisfiability"] is True
    assert all(v != "INCONCLUSIVE" for v in result["State Verdicts"].values())


def test_canonical_fragment_cannot_claim_complete_exhaustion():
    with pytest.raises(ValueError, match="generator='extended'"):
        check_compositional_recall_ast(TwoAgentAdversarialCGS(), ("<{1},3>F", "goal"),
                                      generator="canonical", complete_supported_grammar=True)
