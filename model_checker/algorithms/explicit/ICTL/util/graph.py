"""Graph extraction and model file loading for ICTL."""

import numpy as np

from model_checker.algorithms.explicit.ICTL.util.validation import check_conditions_hold
from model_checker.algorithms.explicit.shared.model_io import (
    SECTION_HANDLERS,
    read_sectioned_model_file,
)


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


def read_file(filename):
    """Load and validate an ICTL model from a text file."""
    data = read_sectioned_model_file(
        filename=filename,
        initial_data={
            "graph": [],
            "states": [],
            "atomic_propositions": [],
            "matrix_prop": [],
            "initial_state": "",
            "states_counter": 0,
            "atomic_propositions_counter": 0,
        },
        section_handlers=SECTION_HANDLERS,
    )

    check_conditions_hold(data)
    return data
