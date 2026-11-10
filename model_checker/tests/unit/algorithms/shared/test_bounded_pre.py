"""Bounded pre-image for RBATL and RABATL: forcing the target in one step within a cost bound.

The model: from s0, agent 1 plays A or B while agent 2 always plays C; AC reaches
s1 (the target) and BC reaches s2. RBATL charges a joint action one cost per
resource; RABATL charges each agent and sums only the coalition's share.
"""

import pytest

from model_checker.algorithms.explicit.shared.bounded_atl_preimage import (
    build_transition_cache,
    compute_pre_states,
)
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS

_MODEL = (
    "Transition\n0 AC BC\n0 ** 0\n0 0 **\nName_State\ns0 s1 s2\nInitial_State\ns0\n"
    "{header}\n{costs}\nAtomic_propositions\np\nLabelling\n0\n1\n0\nNumber_of_agents\n2\n"
)


def _pre(temp_file, header, costs, coalition, bound, cost_filter):
    model = CostCGS()
    model.read_file(temp_file(_MODEL.format(header=header, costs=costs)))
    cache = build_transition_cache(model, coalition)
    return compute_pre_states(model, coalition, {"s1"}, bound, cache, cost_filter)


@pytest.mark.unit
@pytest.mark.parametrize(("bound", "pre"), [([4], {"s1"}), ([5], {"s0", "s1"})])
def test_rbatl_bound_removes_a_move_that_costs_too_much(temp_file, bound, pre):
    """AC costs 5: a bound of 4 takes the only winning move away, 5 keeps it."""
    costs = "AC s0$5\nBC s0$1\n** s1$0;s2$0"
    assert _pre(temp_file, "Costs_for_actions", costs, "1", bound, "rbatl") == pre


@pytest.mark.unit
@pytest.mark.parametrize(
    ("coalition", "bound", "pre"),
    [
        ("1", [1], {"s0", "s1"}),
        ("1", [0], {"s1"}),
        ("1,2", [10], {"s0", "s1"}),
        ("1,2", [9], {"s1"}),
    ],
)
def test_rabatl_counts_only_the_coalition_cost(temp_file, coalition, bound, pre):
    """AC costs agent 1 one unit and agent 2 nine: {1} pays 1, {1,2} pays 10."""
    costs = "AC s0$1,9\nBC s0$1,1\n** s1$0,0;s2$0,0"
    assert (
        _pre(temp_file, "Costs_for_actions_split", costs, coalition, bound, "rabatl")
        == pre
    )


@pytest.mark.unit
def test_rabatl_coalition_whose_move_the_opponent_can_divert(temp_file):
    """Agent 2 plays C in both AC and BC, so agent 1 can escape to s2 whatever the budget."""
    costs = "AC s0$1,9\nBC s0$1,1\n** s1$0,0;s2$0,0"
    assert _pre(temp_file, "Costs_for_actions_split", costs, "2", [100], "rabatl") == {
        "s1"
    }


@pytest.mark.unit
def test_wildcard_cell_to_two_states_does_not_force_either(temp_file):
    """`**` from s0 to both s1 and s2 lets the others pick s2, so s0 is not in pre({s1})."""
    model = CostCGS()
    model.read_file(
        temp_file(
            "Transition\n0 ** **\n0 ** 0\n0 0 **\nName_State\ns0 s1 s2\nInitial_State\ns0\n"
            "Costs_for_actions\n** s0$0;s1$0;s2$0\nAtomic_propositions\np\nLabelling\n0\n1\n0\n"
            "Number_of_agents\n2\n"
        )
    )
    cache = build_transition_cache(model, "1")
    assert compute_pre_states(model, "1", {"s1"}, [5], cache, "rbatl") == {"s1"}
    assert compute_pre_states(model, "1", {"s1", "s2"}, [5], cache, "rbatl") == {
        "s0",
        "s1",
        "s2",
    }


@pytest.mark.unit
@pytest.mark.parametrize("cost_filter", ["rbatl", "rabatl"])
def test_move_that_also_reaches_a_state_outside_the_target_does_not_force(
    test_data_dir, cost_filter
):
    """In the medium fixtures A|A|^ from s0 reaches s1 and s3, so only {s1, s3} is forced."""
    from model_checker.tests.helpers.model_helpers import load_test_model

    logic = cost_filter.upper()
    cgs = load_test_model(
        test_data_dir, f"costCGS/{logic}/{cost_filter}_3agents_medium_6states_costs.txt"
    )
    cache = build_transition_cache(cgs, "1")
    bound = [100, 100, 100]
    assert compute_pre_states(cgs, "1", {"s1"}, bound, cache, cost_filter) == {"s1"}
    assert compute_pre_states(cgs, "1", {"s1", "s3"}, bound, cache, cost_filter) == {
        "s0",
        "s1",
        "s3",
    }
