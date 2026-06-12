"""Validation rules for IATL BCGS models."""

from itertools import combinations

import numpy as np

from model_checker.algorithms.explicit.IATL.preimage import group_moves_by_coalition
from model_checker.parsers.game_structures.cgs import cgs_actions


def _check_graph_shape(graph: np.ndarray) -> None:
    if graph.shape[0] != graph.shape[1]:
        raise AssertionError("The graph is not squared.")


def _check_agent_actions(graph: np.ndarray, num_agents: int) -> None:
    if not all(
        all(len(profile) % num_agents == 0 for profile in str(cell).split(","))
        for row in graph
        for cell in row
        if cell not in (0, "0")
    ):
        raise AssertionError("Some agents don't have available actions in some states.")


def _check_nonzero_rows(graph: np.ndarray) -> None:
    if not np.all(np.any(graph != 0, axis=1)):
        raise AssertionError("zero outer edges from a state")


def _check_idle_action(graph: np.ndarray, num_agents: int) -> None:
    idle_cell = (("I" * num_agents + ",") * num_agents)[:-1]
    if not all(graph[i][i] == idle_cell for i in range(len(graph))):
        raise AssertionError("There's no Idle from some states and some agents")


def _check_preorder_reflective(preorder: np.ndarray) -> None:
    if not np.all(np.diagonal(preorder) == 1):
        raise AssertionError("The preorder is not reflective.")


def _check_preorder_antisymmetric(preorder: np.ndarray) -> None:
    off_diagonal = preorder.copy()
    np.fill_diagonal(off_diagonal, False)
    if np.any(off_diagonal & off_diagonal.T):
        raise AssertionError("The preorder is not antisymmetric.")


def _check_preorder_transitive(preorder: np.ndarray) -> None:
    preorder_int = preorder.astype(np.int8)
    two_step = np.matmul(preorder_int, preorder_int).astype(bool)
    if np.any(two_step & ~preorder):
        raise AssertionError("The preorder is not transitive.")


def _coalition_labels(num_agents: int) -> list:
    """Return every non-empty coalition as a comma-separated agent label."""
    agents = list(range(1, num_agents + 1))
    labels = []
    for size in range(1, num_agents + 1):
        for combo in combinations(agents, size):
            labels.append(",".join(str(agent) for agent in combo))
    return labels


def _coalition_moves_at_state(graph, state_idx, num_agents, coalition_label):
    formatted_agents = cgs_actions.format_agents(
        cgs_actions.get_agents_from_coalition(coalition_label)
    )
    return group_moves_by_coalition(graph[state_idx], num_agents, formatted_agents)


def _decisions_simulate_c1(transitions_i, transitions_j, preorder) -> bool:
    """Every opponent response at j has a matching response at i with forward preorder."""
    opponent_moves_j = {move for move, _ in transitions_j}
    for opp_j in opponent_moves_j:
        for dest_j in {dest for move, dest in transitions_j if move == opp_j}:
            if not any(
                preorder[dest_i, dest_j] == 1
                for opp_i in {move for move, _ in transitions_i}
                for dest_i in {dest for move, dest in transitions_i if move == opp_i}
            ):
                return False
    return True


def _decisions_simulate_c2(transitions_i, transitions_j, preorder) -> bool:
    """Dual of C1: outcomes at j are simulated backward into outcomes at i."""
    opponent_moves_j = {move for move, _ in transitions_j}
    for opp_j in opponent_moves_j:
        for dest_j in {dest for move, dest in transitions_j if move == opp_j}:
            if not any(
                preorder[dest_j, dest_i] == 1
                for opp_i in {move for move, _ in transitions_i}
                for dest_i in {dest for move, dest in transitions_i if move == opp_i}
            ):
                return False
    return True


def _coalition_c1_holds(moves_i, moves_j, preorder, forward_simulate) -> bool:
    """Definition 2 C1 at s_i <= s_j for one coalition."""
    for transitions_i in moves_i.values():
        if not any(
            forward_simulate(transitions_i, transitions_j, preorder)
            for transitions_j in moves_j.values()
        ):
            return False
    return True


def _check_well_behaved_c1(
    graph: np.ndarray, preorder: np.ndarray, num_agents: int
) -> None:
    """C1 (Definition 2): contravariant simulation per coalition along preorder."""
    n = graph.shape[0]
    for coalition in _coalition_labels(num_agents):
        for i in range(n):
            moves_i = _coalition_moves_at_state(graph, i, num_agents, coalition)
            for j in range(n):
                if preorder[i, j] != 1:
                    continue
                moves_j = _coalition_moves_at_state(graph, j, num_agents, coalition)
                if not _coalition_c1_holds(
                    moves_i, moves_j, preorder, _decisions_simulate_c1
                ):
                    raise AssertionError(
                        f"BCGS does not satisfy condition C1 for coalition {coalition}."
                    )


def _check_well_behaved_c2(
    graph: np.ndarray, preorder: np.ndarray, num_agents: int
) -> None:
    """C2 (Definition 2): dual of C1 with reversed preorder on outcomes."""
    n = graph.shape[0]
    for coalition in _coalition_labels(num_agents):
        for i in range(n):
            moves_i = _coalition_moves_at_state(graph, i, num_agents, coalition)
            for j in range(n):
                if preorder[j, i] != 1:
                    continue
                moves_j = _coalition_moves_at_state(graph, j, num_agents, coalition)
                if not _coalition_c1_holds(
                    moves_i, moves_j, preorder, _decisions_simulate_c2
                ):
                    raise AssertionError(
                        f"BCGS does not satisfy condition C2 for coalition {coalition}."
                    )


def _preorder_successors(preorder: np.ndarray, states) -> dict:
    successors = {}
    for i in range(preorder.shape[0]):
        for j in range(preorder.shape[1]):
            if i != j and preorder[i, j] == 1:
                successors.setdefault(states[i], set()).add(states[j])
    return successors


def _check_labeling_respects_preorder(
    preorder_successors, matrix_prop, states_list
) -> None:
    """Labels are monotone along preorder: V(s) subset V(s') when s <= s'."""
    state_index = {str(state): idx for idx, state in enumerate(states_list)}
    for state, greater_states in preorder_successors.items():
        state_row = matrix_prop[state_index[str(state)]]
        for greater_state in greater_states:
            greater_row = matrix_prop[state_index[str(greater_state)]]
            if not np.all((state_row == 0) | (greater_row == 1)):
                raise AssertionError("Labeling function not respected for preorder.")


def _check_model_metadata(data) -> None:
    if data["states_counter"] <= 0:
        raise AssertionError("There's no states in your model.")
    if data["atomic_propositions_counter"] <= 0:
        raise AssertionError("There's no atoms in your model.")
    if data["number_of_agents"] <= 0:
        raise AssertionError("There's no actions in your model.")
    if not np.all(np.isin(data["preorder"], [0, 1])):
        raise AssertionError("Only boolean proposition matrix are admitted.")
    if not np.all(np.isin(data["matrix_prop"], [0, 1])):
        raise AssertionError("Only boolean proposition matrix are admitted.")


def check_conditions_hold(data) -> None:
    """Validate that ``data`` describes a well-formed IATL BCGS model."""
    graph = data["graph"]
    preorder = data["preorder"]
    num_agents = data["number_of_agents"]

    _check_model_metadata(data)
    _check_graph_shape(graph)
    _check_agent_actions(graph, num_agents)
    _check_nonzero_rows(graph)
    _check_idle_action(graph, num_agents)
    _check_preorder_reflective(preorder)
    _check_preorder_antisymmetric(preorder)
    _check_preorder_transitive(preorder)
    _check_well_behaved_c1(graph, preorder, num_agents)
    _check_well_behaved_c2(graph, preorder, num_agents)

    preorder_successors = _preorder_successors(preorder, data["states"])
    _check_labeling_respects_preorder(
        preorder_successors, data["matrix_prop"], data["states"]
    )
