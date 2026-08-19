"""Graph extraction and model file loading for ICTL."""

import numpy as np


def get_preorder(preorder_pairs, states_list):
    """P-upset per state: transitive closure of direct P edges."""
    n_states = len(states_list)
    state_to_idx = {str(state): idx for idx, state in enumerate(states_list)}
    closure = np.zeros((n_states, n_states), dtype=bool)
    for source, dest in preorder_pairs:
        closure[state_to_idx[str(source)], state_to_idx[str(dest)]] = True
    while True:
        two_step = np.matmul(closure.astype(np.int8), closure.astype(np.int8)).astype(
            bool
        )
        expanded = closure | two_step
        if not np.any(expanded & ~closure):
            break
        closure = expanded
    return {
        str(states_list[a]): {
            str(states_list[b]) for b in range(n_states) if closure[a, b]
        }
        for a in range(n_states)
    }
