"""Synthetic ICTL model generators."""

import numpy as np

from model_checker.algorithms.explicit.ICTL.util.validation import check_conditions_hold


def _apply_antisymmetry_transitivity(n_states, states_row, states_col, relations):
    indices = [np.arange(i, n_states, states_col) for i in range(states_col)]
    indices_zigzag = [
        np.concatenate(([indices[states_col - 1][i]], indices[0][i + 1 :]))
        for i in range(states_row)
    ]
    i_index, j_index = zip(
        *[(i, j) for arr in indices for i in arr for j in arr if i < j]
    )
    i_index_z, j_index_z = zip(
        *[(arr[0], j) for arr in indices_zigzag for j in arr if arr[0] < j]
    )
    relations[i_index, j_index] = "P"
    relations[i_index_z, j_index_z] = "P"


def _apply_seriality(n_states, relations, states_col):
    j_indices = [
        np.arange(i, i + states_col - 1) for i in range(0, n_states - states_col + 1)
    ]
    n_extractions = np.random.choice(np.arange(1, states_col))
    i_indices = np.tile(np.arange(states_col - 1, n_states), n_extractions)
    extracted = np.array(
        [[np.random.choice(j) for j in j_indices] for _ in range(n_extractions)]
    ).flatten()
    relations[i_indices, extracted] = "R"


def _apply_zigzag_structure(n_states, relations, states_col):
    index_up_shifted_diagonal = [np.arange(0, n_states - 1), np.arange(1, n_states)]
    preorder_on_up_shifted_diagonal = [
        np.arange(states_col - 1, n_states - 1, states_col),
        np.arange(states_col, n_states, states_col),
    ]
    relation_on_up_shifted_diagonal = [
        np.setdiff1d(index_up_shifted_diagonal[0], preorder_on_up_shifted_diagonal[0]),
        np.setdiff1d(index_up_shifted_diagonal[1], preorder_on_up_shifted_diagonal[1]),
    ]
    relations[
        preorder_on_up_shifted_diagonal[0], preorder_on_up_shifted_diagonal[1]
    ] = "P"
    relations[
        relation_on_up_shifted_diagonal[0], relation_on_up_shifted_diagonal[1]
    ] = "R"


def _square_matrix_reflective(n_states):
    relations = np.full((n_states, n_states), "0", dtype=object)
    np.fill_diagonal(relations, np.random.choice(["P", "P,R"], size=n_states))
    return relations


def _labeling_matrix(n_states, states_col):
    atomic_propositions = np.array(["e", "h", "c"])
    proposition_matrix = np.full((n_states, atomic_propositions.shape[0]), 0)
    indices = np.arange(1, n_states)
    cond1 = indices % states_col == 0
    cond2 = indices % states_col == states_col - 1
    cond3 = ~(cond1 | cond2)
    proposition_matrix[indices[cond1], 1] = 1
    proposition_matrix[indices[cond2], 1] = 1
    proposition_matrix[indices[cond3], 0] = 1
    return proposition_matrix, atomic_propositions, len(atomic_propositions)


def generate_experiment_model(states_row, states_col):
    """Build a birelational experiment model with reflexivity and seriality."""
    if states_col <= 2 or states_row <= 1:
        raise ValueError("Matrix dimensions too small. Minimum supported size is 2x3.")

    n_states = states_row * states_col
    relations = _square_matrix_reflective(n_states)
    _apply_zigzag_structure(n_states, relations, states_col)
    _apply_seriality(n_states, relations, states_col)
    _apply_antisymmetry_transitivity(n_states, states_row, states_col, relations)

    states = np.array([f"s{i}" for i in range(n_states)])
    matrix_prop, atomic_propositions, ap_count = _labeling_matrix(n_states, states_col)
    data = {
        "graph": relations,
        "states": states,
        "atomic_propositions": atomic_propositions,
        "matrix_prop": matrix_prop,
        "initial_state": states[0],
        "states_counter": n_states,
        "atomic_propositions_counter": ap_count,
    }
    check_conditions_hold(data)
    return data
