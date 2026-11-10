"""OL cost semantics: a demon with budget k picks the path, paying each transition's cost.

The chain model: s0 -> s1 -> s2 -> s2, every step costing 1. So the demon can
reach s1 from s0 for 1, s2 for 2, and from s2 it can only stay.
"""

import pytest

from model_checker.algorithms.explicit.OL.preimage import (
    states_globally_in,
    states_release,
    states_until,
    states_with_next_in,
    states_within_cost,
)
from model_checker.algorithms.explicit.shared.cost_utils import transition_cell_cost
from model_checker.tests.helpers.model_helpers import load_costcgs_from_content
from model_checker.tests.helpers.synthetic_models import (
    build_cgs_model_content,
    generate_cost_cgs_linear_chain_content,
)

_ALL = {"s0", "s1", "s2"}


@pytest.fixture
def chain(temp_file):
    return load_costcgs_from_content(
        temp_file, generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
    )


@pytest.mark.unit
def test_cell_cost_comes_from_the_action_or_the_number(chain):
    """An action cell costs what Costs_for_actions says; a numeric cell is its own cost."""
    assert transition_cell_cost(chain, 0, chain.graph[0][1]) == 1.0
    assert transition_cell_cost(chain, 0, 0) == 0.0
    assert transition_cell_cost(chain, 0, 4) == 4.0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("budget", "states"), [(0, {"s2"}), (1, {"s1", "s2"}), (2, _ALL), (5, _ALL)]
)
def test_eventually_is_reachable_within_the_budget(chain, budget, states):
    """F s2 holds where the path to s2 costs at most k: 0 at s2, 1 at s1, 2 at s0."""
    assert states_within_cost(chain, {"s2"}, budget) == states


@pytest.mark.unit
def test_eventually_never_reaches_a_state_behind_the_start(chain):
    """Nothing leads back to s0, so F s0 holds only at s0 for any budget."""
    assert states_within_cost(chain, {"s0"}, 100) == {"s0"}


@pytest.mark.unit
@pytest.mark.parametrize(("budget", "states"), [(0, set()), (1, {"s0"})])
def test_next_needs_an_affordable_step(chain, budget, states):
    """X s1 at s0 needs the step to s1 (cost 1); with budget 0 no step is affordable, so it fails."""
    assert states_with_next_in(chain, {"s1"}, budget) == states


@pytest.mark.unit
def test_next_fails_when_one_affordable_step_leaves_the_target(temp_file):
    """From s0 the demon may pay 1 for s1 or for s2, so X s1 does not hold at s0."""
    content = build_cgs_model_content(
        transitions=[["0", "1A", "2A"], ["0", "*", "0"], ["0", "0", "*"]],
        state_names=["s0", "s1", "s2"],
        initial_state="s0",
        labelling=[["0"], ["1"], ["0"]],
        prop_names=["p"],
        costs_for_actions={"1A": "s0$1:0", "2A": "s0$1:0", "*": "s1$2:0;s2$0:0"},
        num_agents=1,
    )
    cgs = load_costcgs_from_content(temp_file, content)
    assert states_with_next_in(cgs, {"s1"}, 1) == set()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("budget", "states"), [(0, {"s0", "s1"}), (1, {"s0"}), (2, set())]
)
def test_globally_holds_until_the_demon_can_pay_its_way_out(chain, budget, states):
    """G {s0, s1}: leaving to s2 costs 1 from s1 and 2 from s0."""
    assert states_globally_in(chain, {"s0", "s1"}, budget) == states


@pytest.mark.unit
def test_globally_over_every_state_always_holds(chain):
    """With no state outside phi there is nothing to escape to."""
    assert states_globally_in(chain, _ALL, 0) == _ALL


@pytest.mark.unit
@pytest.mark.parametrize(("phi", "states"), [({"s0", "s1"}, _ALL), ({"s0"}, {"s2"})])
def test_until_needs_phi_on_the_way(chain, phi, states):
    """phi U s2 within 2: from s0 the path passes s1, so s1 must be in phi."""
    assert states_until(chain, phi, {"s2"}, 2) == states


@pytest.mark.unit
def test_until_and_eventually_of_nothing_are_empty(chain):
    """No state satisfies an empty target, whatever the budget."""
    assert states_until(chain, _ALL, set(), 5) == set()
    assert states_within_cost(chain, set(), 5) == set()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("phi", "psi", "states"),
    [({"s0", "s1"}, {"s2"}, {"s2"}), ({"s2"}, _ALL, _ALL)],
)
def test_release_keeps_psi_until_phi_frees_it(chain, phi, psi, states):
    """{s0,s1} R s2 holds only at s2, where s2 holds forever; phi R true holds everywhere."""
    assert states_release(chain, phi, psi, 2) == states
