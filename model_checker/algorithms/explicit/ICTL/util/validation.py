"""Validation rules for ICTL birelational models."""

from typing import Any

import numpy as np

from model_checker.algorithms.explicit.shared.graph_relations import labeled_pairs

PREORDER_CELLS = frozenset({"P", "P,R"})
# A star, like R, is a transition to the cell's column.
TRANSITION_CELLS = frozenset({"R", "P,R", "*"})
_KNOWN_CELLS = PREORDER_CELLS | TRANSITION_CELLS | {0, "0"}


def _check_c1(graph: np.ndarray) -> bool:
    """Forward confluence: if s' refines s, each successor of s has a successor of s'
    that is at least as informative."""
    n = graph.shape[0]
    for s in range(n):
        for s_prime in range(n):
            if graph[s, s_prime] not in PREORDER_CELLS:
                continue
            for t in range(n):
                if graph[s, t] not in TRANSITION_CELLS:
                    continue
                if not any(
                    graph[s_prime, t_prime] in TRANSITION_CELLS
                    and graph[t, t_prime] in PREORDER_CELLS
                    for t_prime in range(n)
                ):
                    return False
    return True


def _check_c2(graph: np.ndarray) -> bool:
    """Backward confluence: if s' refines s, each successor of s' has a successor of
    s that is no more informative."""
    n = graph.shape[0]
    for s in range(n):
        for s_prime in range(n):
            if graph[s, s_prime] not in PREORDER_CELLS:
                continue
            for t_prime in range(n):
                if graph[s_prime, t_prime] not in TRANSITION_CELLS:
                    continue
                if not any(
                    graph[s, t] in TRANSITION_CELLS
                    and graph[t, t_prime] in PREORDER_CELLS
                    for t in range(n)
                ):
                    return False
    return True


def _check_graph_shape(graph: np.ndarray) -> None:
    if graph.shape[0] != graph.shape[1]:
        raise AssertionError("The graph is not squared.")


def _check_cells(graph: np.ndarray, states) -> None:
    for (row, column), cell in np.ndenumerate(graph):
        if cell not in _KNOWN_CELLS:
            raise AssertionError(
                f"Transition cell {cell!r} in row {states[row]}, column "
                f"{states[column]} is not 0, R, P, P,R or *."
            )


def _check_serial(graph: np.ndarray) -> None:
    if not all(any(cell in TRANSITION_CELLS for cell in row) for row in graph):
        raise AssertionError("The graph does not satisfy transition serial condition.")


def _check_reflexive(preorder: np.ndarray) -> None:
    if not np.all(preorder[np.diag_indices_from(preorder)]):
        raise AssertionError("The graph is not reflective.")


def _check_antisymmetric(preorder: np.ndarray) -> None:
    off_diagonal = preorder.copy()
    np.fill_diagonal(off_diagonal, False)
    if np.any(off_diagonal & off_diagonal.T):
        raise AssertionError("The graph is not antisymmetric.")


def _check_transitive(preorder: np.ndarray) -> None:
    # Knowledge order must be transitive: if s refines t and t refines u, then s refines u.
    preorder_int = preorder.astype(np.int8)
    two_step = np.matmul(preorder_int, preorder_int).astype(bool)
    if np.any(two_step & ~preorder):
        raise AssertionError("The graph is not transitive.")


def _check_inference_constraints(graph: np.ndarray) -> None:
    if not _check_c1(graph):
        raise AssertionError("The graph does not satisfy condition C1.")
    if not _check_c2(graph):
        raise AssertionError("The graph does not satisfy condition C2.")


def _preorder_successors(graph: np.ndarray, states) -> dict:
    pairs = labeled_pairs(graph, states, PREORDER_CELLS.__contains__)
    successors = {}
    for source, dest in pairs:
        if source != dest:
            successors.setdefault(source, set()).add(dest)
    return successors


def _check_labeling_respects_preorder(
    preorder_successors, matrix_prop, states_list
) -> None:
    """Ensure atoms never disappear when knowledge grows along the preorder."""
    state_index = {str(state): idx for idx, state in enumerate(states_list)}
    for state, greater_states in preorder_successors.items():
        state_row = matrix_prop[state_index[state]]
        for greater_state in greater_states:
            greater_row = matrix_prop[state_index[greater_state]]
            if not np.all((state_row == 0) | (greater_row == 1)):
                raise AssertionError("Labeling function not respected for preorder.")


def _check_model_metadata(model: Any) -> None:
    if len(model.states) <= 0:
        raise AssertionError("There's no states in your model.")
    if len(model.atomic_propositions) <= 0:
        raise AssertionError("There's no atoms in your model.")
    if not np.all(np.isin(model.matrix_prop, [0, 1])):
        raise AssertionError("Only boolean proposition matrix are admitted.")


def check_conditions_hold(model: Any) -> None:
    """Reject a model that is not an ICTL birelational frame: serial transitions, a
    partial knowledge order, confluence C1/C2 and monotone labelling."""
    graph = model.graph
    preorder = np.vectorize(PREORDER_CELLS.__contains__, otypes=[bool])(graph)

    _check_model_metadata(model)
    _check_graph_shape(graph)
    _check_cells(graph, model.states)
    _check_serial(graph)
    _check_reflexive(preorder)
    _check_antisymmetric(preorder)
    _check_transitive(preorder)
    _check_inference_constraints(graph)

    preorder_successors = _preorder_successors(graph, model.states)
    _check_labeling_respects_preorder(
        preorder_successors, model.matrix_prop, model.states
    )
