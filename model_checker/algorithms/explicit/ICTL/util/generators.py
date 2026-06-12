"""Synthetic ICTL benchmark model generators."""

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


def _3k_square_matrix_reflective(k):
    relations = np.full((k * 3, k * 3), "0", dtype=object)
    np.fill_diagonal(relations, np.tile(["P,R", "P", "P,R"], k))
    return relations


def _apply_3k_structure(k, relations):
    for i in range(k):
        offset = 3 * (i - 1)
        if k > 1 and offset > 0:
            relations[offset][offset + 3] = "P"
            relations[offset + 1][offset + 4] = "P"
            relations[offset + 2][offset + 5] = "P"
        relations[offset][offset + 1] = relations[offset + 1][offset + 2] = "R"


def _apply_3k_transitivity(k, relations):
    indices = [np.arange(i, 3 * k, 3) for i in range(3)]
    i_index, j_index = zip(
        *[(i, j) for arr in indices for i in arr for j in arr if i < j]
    )
    relations[i_index, j_index] = "P"


def _3k_labeling_matrix(data, n, dims):
    matrix_proposition = np.zeros(
        (data["states_counter"], data["atomic_propositions_counter"])
    )
    counts = np.arange(1, n + 1)
    total_ones = counts.sum()
    col_ind = np.repeat(np.arange(n), counts)
    row_ind = np.arange(0, 3 * total_ones, 3)
    matrix_proposition[row_ind, col_ind] = 1

    states_an = list(range(2, data["states_counter"], 3))
    repetitions = []
    for i in range(1, n + 1):
        repetitions.extend(range(1, i + 1))
    for i, state_idx in enumerate(states_an):
        for j in range(repetitions[i]):
            matrix_proposition[state_idx][j + n] = 1

    offset = 0
    for block_size in dims:
        matrix_proposition[block_size - 1 + offset, -1] = 1
        matrix_proposition[block_size - 1 + offset, -2] = 1
        matrix_proposition[block_size - 4 + offset, -2] = 1
        offset += block_size

    return matrix_proposition


def merge_3k_graphs(n):
    """Merge 3k experiment graphs (k=1..n) into one transition matrix."""
    matrices = []
    for k in range(1, n + 1):
        relations = _3k_square_matrix_reflective(k)
        _apply_3k_structure(k, relations)
        if k > 1:
            _apply_3k_transitivity(k, relations)
        matrices.append(relations)

    dims = [m.shape[0] for m in matrices]
    big_matrix = np.full((sum(dims), sum(dims)), "0", dtype=object)
    offsets = []
    offset = 0
    for mat in matrices:
        size = mat.shape[0]
        big_matrix[offset : offset + size, offset : offset + size] = mat
        offsets.append(offset)
        offset += size

    j_index = np.array([o - 1 for o in offsets[1:]])
    for i in range(len(j_index) - 1):
        x = j_index[i]
        y = j_index[i + 1]
        for r in range(x + 3, y, 3):
            big_matrix[r, x] = "P"

    return np.array(big_matrix), dims


def generate_3n_model(n):
    """Build the merged 3n benchmark model used in scalability experiments."""
    data = {}
    data["graph"], dims = merge_3k_graphs(n)
    data["states"] = np.array([f"s{i}" for i in range(data["graph"].shape[0])])
    data["states_counter"] = len(data["states"])
    data["initial_state"] = data["states"][data["states_counter"] - 3]
    data["atomic_propositions"] = np.concatenate(
        [
            np.array([f"p{i}" for i in range(n)]),
            np.array([f"an{i}" for i in range(n)]),
            np.array(["know", "yes"]),
        ]
    )
    data["atomic_propositions_counter"] = len(data["atomic_propositions"])
    data["matrix_prop"] = _3k_labeling_matrix(data, n, dims)
    return data
