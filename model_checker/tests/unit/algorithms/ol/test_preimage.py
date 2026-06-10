"""OL cost semantics: transition costs and bounded operators."""

import pytest

from model_checker.algorithms.explicit.OL.preimage import (
    states_globally_in,
    states_release,
    states_until,
    states_weak,
    states_with_next_in,
    states_within_cost,
)
from model_checker.algorithms.explicit.shared.cost_utils import transition_cell_cost
from model_checker.algorithms.explicit.shared.state_utils import state_names_to_indices
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestOLCostSemantics:
    """Core OL cost computations on programmatic fixtures."""

    def test_transition_cell_cost_resolves_action_and_numeric_cells(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)
        s0_idx = list(state_names_to_indices(cgs, {"s0"}))[0]
        action_cell = cgs.graph[s0_idx][1]

        assert transition_cell_cost(cgs, s0_idx, action_cell) == 1.0
        assert transition_cell_cost(cgs, s0_idx, 0) == 0.0
        assert transition_cell_cost(cgs, s0_idx, 4) == 4.0

    def test_eventually_uses_accumulated_transition_costs(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        assert states_within_cost(cgs, {"s2"}, 0) == {"s2"}
        assert states_within_cost(cgs, {"s2"}, 1) == {"s1", "s2"}
        assert states_within_cost(cgs, {"s2"}, 2) == {"s0", "s1", "s2"}

    def test_next_requires_all_affordable_successors(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        assert states_with_next_in(cgs, {"s1"}, 0) == set()
        assert states_with_next_in(cgs, {"s1"}, 1) == {"s0"}

    def test_next_rejects_branch_with_bad_affordable_successor(self, temp_file):
        content = build_cgs_model_content(
            transitions=[
                ["0", "1A", "2A"],
                ["0", "0", "0"],
                ["0", "0", "*"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["1"], ["0"]],
            prop_names=["p"],
            costs_for_actions={"1A": "s0$1:0", "2A": "s0$1:0", "*": "s2$0:0"},
            num_agents=1,
        )
        cgs = load_costcgs_from_content(temp_file, content)

        assert states_with_next_in(cgs, {"s1"}, 1) == set()

    def test_globally_excludes_states_with_cheap_violation(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)
        safe = {"s0", "s1"}

        globally_one = states_globally_in(cgs, safe, 1)
        assert "s0" in globally_one
        assert "s1" not in globally_one
        assert "s0" not in states_globally_in(cgs, safe, 2)

    def test_until_requires_phi_on_prefix(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        assert states_until(cgs, {"s0", "s1"}, {"s2"}, 2) == {"s0", "s1", "s2"}
        assert states_until(cgs, {"s0"}, {"s2"}, 2) == {"s2"}

    def test_release_is_dual_of_until(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)
        phi = {"s0", "s1"}
        psi = {"s2"}
        all_states = {str(s) for s in cgs.all_states_set}
        not_phi = all_states - phi
        not_psi = all_states - psi

        release = states_release(cgs, phi, psi, 2)
        dual = all_states - states_until(cgs, not_phi, not_psi, 2)
        assert release == dual

    def test_weak_matches_release_identity(self, temp_file):
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)
        phi = {"s0"}
        psi = {"s2"}

        assert states_weak(cgs, phi, psi, 2) == states_release(cgs, phi | psi, psi, 2)
