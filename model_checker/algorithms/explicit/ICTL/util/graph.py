"""Graph extraction and model file loading for ICTL."""

import numpy as np

_SECTION_HANDLERS = {
    "Transition": lambda data, line: data["graph"].append(line.split()),
    "Name_State": lambda data, line: data["states"].extend(line.split()),
    "Initial_State": lambda data, line: data.update({"initial_state": line}),
    "Atomic_propositions": lambda data, line: data["atomic_propositions"].extend(
        line.split()
    ),
    "Labelling": lambda data, line: data["matrix_prop"].append(line.split()),
}


def labeled_pairs(relations, states_list, predicate):
    return [
        (
            (states_list[i], states_list[i])
            if element == "*"
            else (states_list[i], states_list[j])
        )
        for i, row in enumerate(relations)
        for j, element in enumerate(row)
        if predicate(element)
    ]


def get_preorder(preorder_pairs, states_list):
    """Upward closure per state from preorder edge pairs."""
    n_states = len(states_list)
    state_to_idx = {str(state): idx for idx, state in enumerate(states_list)}
    upward = np.zeros((n_states, n_states))
    for source, dest in preorder_pairs:
        upward[state_to_idx[str(source)], state_to_idx[str(dest)]] = 1
    return {
        str(states_list[a]): {
            str(states_list[b]) for b in range(n_states) if upward[a, b]
        }
        for a in range(n_states)
    }


def read_file(filename):
    """Load and validate an ICTL model from a text file."""
    with open(filename, encoding="utf-8") as handle:
        lines = handle.readlines()

    data = {
        "graph": [],
        "states": [],
        "atomic_propositions": [],
        "matrix_prop": [],
        "initial_state": "",
        "states_counter": 0,
        "atomic_propositions_counter": 0,
    }

    section = None
    for raw_line in lines:
        line = raw_line.strip()
        if line in _SECTION_HANDLERS:
            section = line
        elif section is not None:
            _SECTION_HANDLERS[section](data, line)

    data["states_counter"] = len(data["states"])
    data["atomic_propositions_counter"] = len(data["atomic_propositions"])
    data["graph"] = np.array(data["graph"])
    data["states"] = np.array(data["states"])
    data["atomic_propositions"] = np.array(data["atomic_propositions"])
    data["matrix_prop"] = np.array(data["matrix_prop"], dtype=int)

    from model_checker.algorithms.explicit.ICTL.util.validation import (
        check_conditions_hold,
    )

    check_conditions_hold(data)
    return data
