"""OL semantics of ECAI 2023: each step the Demon disables edges costing at most n in
total, never all edges of a state, and every remaining path must satisfy the formula.

Expected sets are worked out by hand from Definitions 3-4 and the fixpoints of
Theorem 1, not copied from the checker.
"""

import pytest

from model_checker.algorithms.explicit.OL.OL import model_checking
from model_checker.utils.literals import parse_state_set_literal


def _states(test_data_dir, fixture, formula):
    result = model_checking(formula, str(test_data_dir / "costCGS" / "OL" / fixture))
    assert "error" not in result, result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


@pytest.mark.unit
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "formula",
    [
        "INVALID_FORMULA",
        "<J1> F nonexistent",
        "<JF r",
        "F r",
        "<2> F r",
    ],
)
def test_ol_rejects_invalid_input(test_data_dir, formula):
    model_file = (
        test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
    )
    result = model_checking(formula, str(model_file))
    assert "error" in result


@pytest.mark.semantic
@pytest.mark.model_checking
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        # Disabling the edges to s1 and s3 costs 2 + 1, so s0 needs a budget of 3.
        ("<J2> X goal", {"s2"}),
        ("<J3> X goal", {"s0", "s2"}),
        ("<J2> F goal", {"s2"}),
        ("<J3> F goal", {"s0", "s2"}),
        ("<J2> G !bad", {"s2"}),
        ("<J3> G !bad", {"s0", "s2"}),
        # s2 loops on goal, so it needs no budget at all.
        ("<J0> X goal", {"s2"}),
        # bad R (!goal || bad): s0 must disable its edge to goal s2, which costs 1.
        ("<J0> !goal W bad", {"s1", "s3"}),
        ("<J1> !goal W bad", {"s0", "s1", "s3"}),
        ("<J1> bad R (!goal || bad)", {"s0", "s1", "s3"}),
    ],
)
def test_the_demon_budget_decides(test_data_dir, formula, expected):
    """A formula holds at s0 once the bound pays for disabling every edge that breaks it."""
    assert _states(test_data_dir, "ol_demon_1agent_4states.txt", formula) == expected


_CHAIN_UP_TO_GOAL = {str(i) for i in range(7)}


@pytest.mark.semantic
@pytest.mark.model_checking
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("<J1> F goal", _CHAIN_UP_TO_GOAL),
        ("<J30> F (safe && goal)", _CHAIN_UP_TO_GOAL),
        # 6 -> 7 leaves safe, so no state stays safe forever.
        ("<J30> G safe", set()),
        ("<J30> X safe", {"0", "2", "5"}),
        ("<J30> safe U goal", {"6"}),
        ("<J30> !goal U goal", _CHAIN_UP_TO_GOAL),
        # goal R (!goal || goal) is goal R true, which holds everywhere.
        ("<J30> !goal W goal", {str(i) for i in range(8)}),
        ("<J30> (a_w W goal)", {"6"}),
        ("<J30> (goal R (a_w || goal))", {"6"}),
    ],
)
def test_one_edge_per_state_leaves_the_demon_nothing_to_disable(
    test_data_dir, formula, expected
):
    """The testvitamin model is the chain 0 -> 1 -> ... -> 7 -> 7; any bound reads as CTL's A."""
    fixture = "ol_testvitamin_2agents_8states.txt"
    assert _states(test_data_dir, fixture, formula) == expected


@pytest.mark.semantic
@pytest.mark.model_checking
@pytest.mark.parametrize(
    ("formula", "expected"), [("<J1> X goal", {"s2"}), ("<J2> X goal", {"s0", "s2"})]
)
def test_edge_costs_from_transition_with_costs(test_data_dir, formula, expected):
    """A Transition_With_Costs cell is one edge; its agents' costs 1:1 add up to 2."""
    fixture = "ol_edge_costs_2agents_3states.txt"
    assert _states(test_data_dir, fixture, formula) == expected


_TWO_STATES = (
    "Name_State\ns0 s1\nInitial_State\ns0\nAtomic_propositions\np\n"
    "Labelling\n0\n1\nNumber_of_agents\n1\n"
)


@pytest.mark.model_checking
@pytest.mark.parametrize(
    ("transitions", "message"),
    [
        ("Transition_With_Costs\n5 0:0\n0 1\n", "edge s0 -> s1"),
        ("Transition_With_Costs\n5 00\n0 1\n", "edge s0 -> s1"),
        ("Transition_With_Costs\n5 -1\n0 1\n", "Cost -1 for the edge s0 -> s1"),
        (
            "Transition\nA B\n0 C\nCosts_for_actions\nA s0$5\nB s0$0\nC s1$1\n",
            "B at s0",
        ),
        ("Transition_With_Costs\n5 1\n0 *\n", "self-loop as a cost on the diagonal"),
    ],
)
def test_edge_without_a_positive_cost_is_a_model_error(temp_file, transitions, message):
    """Edge costs are positive integers; a free edge would let <J0> disable it."""
    model_file = temp_file(transitions + _TWO_STATES)
    error = model_checking("<J0> G !p", model_file)["error"]
    assert error["type"] == "model"
    assert message in error["message"]


@pytest.mark.model_checking
def test_a_missing_cost_that_decides_the_result_is_a_model_error(test_data_dir):
    """At s1 the edge to s2 has no cost, so whether the Demon can pay to block it is unknown."""
    model_file = (
        test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
    )
    error = model_checking("<J2> X r", str(model_file))["error"]
    assert error["type"] == "model"
    assert "at states ['s1']" in error["message"]


@pytest.mark.semantic
@pytest.mark.model_checking
def test_every_path_reaches_r_without_budget(test_data_dir):
    """The longest path avoiding r is s0 -> s2 -> s4, whose successors are all r, so AF r holds everywhere."""
    fixture = "ol_2agents_medium_6states_costs.txt"
    assert _states(test_data_dir, fixture, "<J0> F r") == {f"s{i}" for i in range(6)}
