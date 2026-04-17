"""CTL performance: large state spaces, linear/cyclic/fully-connected graphs, fixpoint and pre-image."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.algorithms.explicit.CTL.preimage import pre_image_exist
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    generate_cycle_model,
    generate_linear_chain,
    load_cgs_from_content,
)
from model_checker.tests.performance.performance_helpers import (
    run_model_checking_with_timeout,
)


def generate_fully_connected_model(num_states, num_agents=2, prop_name="p"):
    """Generate a fully connected model where every state can reach every other state.

    Args:
        num_states: Number of states
        num_agents: Number of agents (default 2)
        prop_name: Atomic proposition name (default "p")

    Returns:
        String content of CGS model file
    """
    states = [f"s{i}" for i in range(num_states)]

    transitions = []
    unknown_transitions = []

    for i in range(num_states):
        row = []
        unknown_row = []
        for j in range(num_states):
            if i != j:  # Can transition to any other state
                action = "AC" * num_agents if num_agents == 2 else "AC"
                row.append(action)
            else:  # Self-loop
                row.append("*")
            unknown_row.append("0")
        transitions.append(" ".join(row))
        unknown_transitions.append(" ".join(unknown_row))

    labelling = []
    for i in range(num_states):
        if i < num_states // 2:
            labelling.append("1")
        else:
            labelling.append("0")

    model_content = f"""Transition
{chr(10).join(transitions)}
Unknown_Transition_by
{chr(10).join(unknown_transitions)}
Name_State
{' '.join(states)}
Initial_State
s0
Atomic_propositions
{prop_name}
Labelling
{chr(10).join(labelling)}
Number_of_agents
{num_agents}
"""
    return model_content


def generate_sparse_graph_model(
    num_states, num_agents=2, prop_name="p", connectivity=0.3
):
    """Generate a sparse graph model with limited connectivity.

    Args:
        num_states: Number of states
        num_agents: Number of agents (default 2)
        prop_name: Atomic proposition name (default "p")
        connectivity: Probability of edge between states (0.0 to 1.0)

    Returns:
        String content of CGS model file
    """
    import random

    random.seed(42)  # For reproducibility

    states = [f"s{i}" for i in range(num_states)]

    transitions = []
    unknown_transitions = []

    for i in range(num_states):
        row = []
        unknown_row = []
        for j in range(num_states):
            if i == j:
                row.append("*")  # Self-loop always present
            elif random.random() < connectivity:
                action = "AC" * num_agents if num_agents == 2 else "AC"
                row.append(action)
            else:
                row.append("0")
            unknown_row.append("0")
        transitions.append(" ".join(row))
        unknown_transitions.append(" ".join(unknown_row))

    labelling = []
    for _i in range(num_states):
        if random.random() < 0.3:  # 30% of states have p
            labelling.append("1")
        else:
            labelling.append("0")

    model_content = f"""Transition
{chr(10).join(transitions)}
Unknown_Transition_by
{chr(10).join(unknown_transitions)}
Name_State
{' '.join(states)}
Initial_State
s0
Atomic_propositions
{prop_name}
Labelling
{chr(10).join(labelling)}
Number_of_agents
{num_agents}
"""
    return model_content


def compute_fixpoint_iterations(cgs, target_states, operator="EF"):
    """Compute fixpoint iterations for tracking convergence.

    Args:
        cgs: CGS model instance
        target_states: Set of target state names
        operator: CTL operator ("EF", "EG", "AF", "AG")

    Returns:
        Tuple of (final_result, num_iterations)
    """
    edges = cgs.get_edges()
    all_states = set(cgs.states)

    if operator == "EF":
        T = target_states.copy()
        iterations = 0
        while True:
            new_T = T.union(pre_image_exist(edges, T))
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return T, iterations

    elif operator == "EG":
        T = all_states.copy()
        iterations = 0
        while True:
            new_T = target_states.intersection(pre_image_exist(edges, T))
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return T, iterations

    elif operator == "AF":
        not_target = all_states - target_states
        T = all_states.copy()
        iterations = 0
        while True:
            new_T = not_target.intersection(pre_image_exist(edges, T))
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return all_states - T, iterations

    elif operator == "AG":
        not_target = all_states - target_states
        T = not_target.copy()
        iterations = 0
        while True:
            new_T = T.union(pre_image_exist(edges, T))
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return all_states - T, iterations

    return None, 0


def _model_content_for_ctl(layout, num_states, num_agents=2):
    """Build model content for CTL performance cases."""
    if layout == "linear":
        return generate_linear_chain(num_states, num_agents, action_label="AC")
    if layout == "cycle":
        return generate_cycle_model(num_states, num_agents)
    if layout == "fully_connected":
        return generate_fully_connected_model(num_states, num_agents)
    if layout == "linear_pq":
        return generate_linear_chain(
            num_states, num_agents, prop_names=["p", "q"], action_label="AC"
        )
    raise ValueError(f"Unknown layout: {layout}")


CTL_PERFORMANCE_CASES = [
    ("linear", 100, "EF p", 5.0),
    ("cycle", 100, "EG p", 5.0),
    ("linear", 100, "AF p", 5.0),
    ("linear", 100, "AG p", 5.0),
    ("fully_connected", 100, "EX p", 2.0),
    ("fully_connected", 100, "AX p", 2.0),
    ("linear_pq", 100, "E[p U q]", 5.0),
    ("linear", 200, "EF p", 10.0),
]


@pytest.mark.performance
@pytest.mark.model_checking
class TestCTLPerformanceLargeModels:
    """Performance tests for CTL operators with large state spaces."""

    @pytest.mark.parametrize(
        "layout,num_states,formula,max_time",
        CTL_PERFORMANCE_CASES,
        ids=[
            "ef_linear_100",
            "eg_cycle_100",
            "af_linear_100",
            "ag_linear_100",
            "ex_fully_connected_100",
            "ax_fully_connected_100",
            "eu_linear_100",
            "ef_linear_200",
        ],
    )
    def test_ctl_operator_scales(
        self, temp_file, layout, num_states, formula, max_time
    ):
        """CTL operators complete within time bound."""
        model_content = _model_content_for_ctl(layout, num_states)
        parser = load_cgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, formula, max_time
        )
        assert states is not None
        if formula == "AX p":
            assert states == set()
        else:
            assert len(states) > 0, f"{formula} should hold in some states"

    def test_ef_linear_chain_100_states(self, temp_file):
        """Test EF operator on linear chain with 100 states.

        Verifies:
        - Algorithm completes in reasonable time
        - Convergence happens in expected iterations (at most num_states)
        - Result is correct (all states should satisfy EF p)
        """
        num_states = 100
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {"s0", f"s{num_states - 1}"}

        states, elapsed_time = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "EF p", 5.0
        )

        assert states == {f"s{i}" for i in range(num_states)}, (
            "EF p should hold in all states of the linear chain, "
            f"got {len(states)} states"
        )

        _, iterations = compute_fixpoint_iterations(parser, target_states, "EF")
        assert iterations <= num_states, (
            f"EF fixpoint should converge in at most {num_states} iterations, "
            f"got {iterations}"
        )

    def test_eg_cycle_100_states(self, temp_file):
        """Test EG operator on cycle with 100 states.

        Verifies:
        - Greatest fixpoint converges correctly
        - All states in cycle satisfy EG p
        - Algorithm scales appropriately
        """
        num_states = 100
        model_content = generate_cycle_model(num_states)
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {f"s{i}" for i in range(num_states)}

        states, elapsed_time = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "EG p", 5.0
        )

        assert (
            len(states) == num_states
        ), f"EG p should hold in all {num_states} states, got {len(states)}"

        _, iterations = compute_fixpoint_iterations(parser, target_states, "EG")
        assert iterations <= num_states, (
            f"EG fixpoint should converge in at most {num_states} iterations, "
            f"got {iterations}"
        )

    def test_af_linear_chain_100_states(self, temp_file):
        """Test AF operator on linear chain with 100 states.

        Verifies:
        - AF (greatest fixpoint) converges correctly
        - All states satisfy AF p (all paths eventually reach p)
        """
        num_states = 100
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {"s0", f"s{num_states - 1}"}

        states, elapsed_time = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "AF p", 5.0
        )

        assert states == {
            f"s{i}" for i in range(num_states)
        }, "AF p should hold in all states of the linear chain"

        _, iterations = compute_fixpoint_iterations(parser, target_states, "AF")
        assert iterations <= num_states, (
            f"AF fixpoint should converge in at most {num_states} iterations, "
            f"got {iterations}"
        )

    def test_ag_linear_chain_100_states(self, temp_file):
        """Test AG operator on linear chain with 100 states.

        Verifies:
        - AG (least fixpoint via complement) converges correctly
        - Only states where p holds globally satisfy AG p
        """
        num_states = 100
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {"s0", f"s{num_states - 1}"}

        states, elapsed_time = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "AG p", 5.0
        )

        assert states == {
            f"s{num_states - 1}"
        }, "AG p should hold only in terminal state"

        _, iterations = compute_fixpoint_iterations(parser, target_states, "AG")
        assert iterations <= num_states, (
            f"AG fixpoint should converge in at most {num_states} iterations, "
            f"got {iterations}"
        )

    def test_ex_fully_connected_100_states(self, temp_file):
        """Test EX operator on fully connected graph with 100 states.

        Verifies:
        - Pre-image computation scales with large transition sets
        - EX operator handles many successors efficiently
        """
        num_states = 100
        model_content = generate_fully_connected_model(num_states)
        parser = load_cgs_from_content(temp_file, model_content)

        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "EX p", 2.0
        )

        assert states == {
            f"s{i}" for i in range(num_states)
        }, "EX p should hold in every state of the fully connected graph"

    def test_ax_fully_connected_100_states(self, temp_file):
        """Test AX operator on fully connected graph with 100 states.

        Verifies:
        - Universal pre-image computation scales appropriately
        - AX operator handles many successors efficiently
        """
        num_states = 100
        model_content = generate_fully_connected_model(num_states)
        parser = load_cgs_from_content(temp_file, model_content)

        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "AX p", 2.0
        )
        assert (
            states == set()
        ), "AX p should hold in no states (successors include non-p)"

    def test_eu_linear_chain_100_states(self, temp_file):
        """Test EU operator on linear chain with 100 states.

        Verifies:
        - EU (least fixpoint) converges correctly
        - Until operator scales with large state spaces
        """
        num_states = 100
        # Generate model with both p and q propositions
        model_content = generate_linear_chain(
            num_states, prop_names=["p", "q"], action_label="AC"
        )
        parser = load_cgs_from_content(temp_file, model_content)

        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "E[p U q]", 5.0
        )

        assert states == {
            f"s{num_states - 1}"
        }, "E[p U q] should hold only in state with q"

    def test_sparse_graph_150_states(self, temp_file):
        """Test multiple operators on sparse graph with 150 states.

        Verifies:
        - Algorithms handle realistic sparse topologies
        - Performance is acceptable even with larger state spaces
        """
        num_states = 150
        model_content = generate_sparse_graph_model(num_states, connectivity=0.2)
        parser = load_cgs_from_content(temp_file, model_content)

        operators = ["EF p", "EG p", "AF p", "AG p", "EX p", "AX p"]

        for formula in operators:
            states, _ = run_model_checking_with_timeout(
                parser, _core_ctl_checking, formula, 10.0
            )

    def test_large_model_200_states_linear(self, temp_file):
        """Test with 200 states in linear chain.

        Verifies:
        - Algorithms scale to 200+ states
        - Convergence is still bounded by state count
        """
        num_states = 200
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {"s0", f"s{num_states - 1}"}

        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, "EF p", 10.0
        )

        assert states == {
            f"s{i}" for i in range(num_states)
        }, "EF p should hold in all states of the 200-state linear chain"

        _, iterations = compute_fixpoint_iterations(parser, target_states, "EF")
        assert (
            iterations <= num_states
        ), f"EF fixpoint should converge in at most {num_states} iterations"

    def test_fixpoint_convergence_guarantee(self, temp_file):
        """Test that fixpoints always converge in finite steps.

        This is a fundamental property: fixpoints must converge in at most |S| iterations.
        """
        num_states = 100
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        target_states = {"s0", f"s{num_states - 1}"}

        operators = ["EF", "EG", "AF", "AG"]
        for op in operators:
            _, iterations = compute_fixpoint_iterations(parser, target_states, op)
            assert iterations <= num_states, (
                f"{op} fixpoint should converge in at most {num_states} iterations, "
                f"got {iterations}"
            )

    def test_correctness_large_models(self, temp_file):
        """Verify that large models produce correct results.

        Compares results from large models with manually verifiable properties.
        """
        num_states = 100
        model_content = generate_linear_chain(num_states, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)

        result = _core_ctl_checking(parser, "EF p")
        states = extract_states_from_result(result)
        assert states is not None
        assert states == {
            f"s{i}" for i in range(num_states)
        }, "EF p should hold in all states of the linear chain"

        result = _core_ctl_checking(parser, "EX p")
        states = extract_states_from_result(result)
        assert states is not None
        expected_ex_states = {f"s{num_states - 2}", f"s{num_states - 1}"}
        assert (
            states == expected_ex_states
        ), "EX p should hold only in states with a direct transition to a p-state"
