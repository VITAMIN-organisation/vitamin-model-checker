"""Validation rules for ICTL birelational models."""

import numpy as np

from model_checker.algorithms.explicit.ICTL.util.graph import labeled_pairs

_PREORDER_CELLS = frozenset({"P", "P,R"})
_TRANSITION_CELLS = frozenset({"R", "P,R"})


def _check_birelational_constraint(
    graph,
    row_indices,
    col_indices,
    row_symbols,
    col_symbols,
) -> bool:
    """Check one of the C1/C2/C3 birelational inference constraints."""
    row_symbols = set(row_symbols)
    col_symbols = set(col_symbols)
    return all(
        any(
            not all(
                graph[row_idx, col_idx] in col_symbols
                and graph[col_idx, row_idx] in row_symbols
                for col_idx in col_indices
            )
            for row_idx in row_indices
            if any(graph[row_idx, col_idx] in row_symbols for col_idx in col_indices)
        )
        for col_idx in col_indices
        if any(graph[row_idx, col_idx] in col_symbols for row_idx in row_indices)
    )


def _check_graph_shape(graph: np.ndarray) -> None:
    if graph.shape[0] != graph.shape[1]:
        raise AssertionError("The graph is not squared.")


def _check_serial(graph: np.ndarray) -> None:
    if not all(any(cell in _TRANSITION_CELLS for cell in row) for row in graph):
        raise AssertionError("The graph does not satisfy transition serial condition.")


def _check_reflexive(graph: np.ndarray, preorder: np.ndarray) -> None:
    if not np.all(preorder[np.diag_indices_from(preorder)]):
        raise AssertionError("The graph is not reflective.")


def _check_antisymmetric(preorder: np.ndarray) -> None:
    off_diagonal = preorder.copy()
    np.fill_diagonal(off_diagonal, False)
    if np.any(off_diagonal & off_diagonal.T):
        raise AssertionError("The graph is not antisymmetric.")


def _check_transitive(preorder: np.ndarray) -> None:
    # If s ->p t ->p u then s ->p u (boolean matrix multiply = 2-step preorder paths).
    preorder_int = preorder.astype(np.int8)
    two_step = np.matmul(preorder_int, preorder_int).astype(bool)
    if np.any(two_step & ~preorder):
        raise AssertionError("The graph is not transitive.")


def _check_inference_constraints(graph: np.ndarray) -> None:
    n = graph.shape[0]
    indices = range(n)
    transition_preorder = ["R", "P,R"]
    preorder_transition = ["P", "P,R"]

    if not _check_birelational_constraint(
        graph, indices, indices, transition_preorder, preorder_transition
    ):
        raise AssertionError("The graph does not satisfy conditions C1 and C2.")
    if not _check_birelational_constraint(
        graph, indices, indices, preorder_transition, transition_preorder
    ):
        raise AssertionError("The graph does not satisfy condition C3.")


def _preorder_successors(graph: np.ndarray, states) -> dict:
    pairs = labeled_pairs(graph, states, lambda cell: cell in _PREORDER_CELLS)
    successors = {}
    for source, dest in pairs:
        if source != dest:
            successors.setdefault(source, set()).add(dest)
    return successors


def _check_labeling_respects_preorder(
    preorder_successors, matrix_prop, states_list
) -> None:
    """Labels are monotone along preorder: V(s) subset V(s') when s <= s'."""
    state_index = {str(state): idx for idx, state in enumerate(states_list)}
    for state, greater_states in preorder_successors.items():
        state_row = matrix_prop[state_index[state]]
        for greater_state in greater_states:
            greater_row = matrix_prop[state_index[greater_state]]
            if not np.all((state_row == 0) | (greater_row == 1)):
                raise AssertionError("Labeling function not respected for preorder.")


def _check_model_metadata(data) -> None:
    if data["states_counter"] <= 0:
        raise AssertionError("There's no states in your model.")
    if data["atomic_propositions_counter"] <= 0:
        raise AssertionError("There's no atoms in your model.")
    if not np.all(np.isin(data["matrix_prop"], [0, 1])):
        raise AssertionError("Only boolean proposition matrix are admitted.")


def check_conditions_hold(data) -> None:
    """Validate that ``data`` describes a well-formed ICTL birelational model."""
    graph = data["graph"]
    preorder = np.vectorize(lambda cell: cell in _PREORDER_CELLS, otypes=[bool])(graph)

    _check_model_metadata(data)
    _check_graph_shape(graph)
    _check_serial(graph)
    _check_reflexive(graph, preorder)
    _check_antisymmetric(preorder)
    _check_transitive(preorder)
    _check_inference_constraints(graph)

    preorder_successors = _preorder_successors(graph, data["states"])
    _check_labeling_respects_preorder(
        preorder_successors, data["matrix_prop"], data["states"]
    )
