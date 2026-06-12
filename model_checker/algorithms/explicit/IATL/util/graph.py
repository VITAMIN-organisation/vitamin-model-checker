"""Graph extraction and model file loading for IATL BCGS models."""

import numpy as np

_SECTION_HANDLERS = {
    "Transition": lambda data, line: data["graph"].append(line.split()),
    "Preorder": lambda data, line: data["preorder"].append(line.split()),
    "Name_State": lambda data, line: data["states"].extend(line.split()),
    "Initial_State": lambda data, line: data.update({"initial_state": line}),
    "Atomic_propositions": lambda data, line: data["atomic_propositions"].extend(
        line.split()
    ),
    "Labelling": lambda data, line: data["matrix_prop"].append(line.split()),
    "Number_of_agents": lambda data, line: data.update({"number_of_agents": int(line)}),
}


def get_actions(graph, agents):
    """Extract per-agent action sets from the BCGS transition matrix."""

    def process_elem(elem):
        if elem in (0, "*", "0"):
            return [[], []]
        action_profiles = elem.split(",")
        return [
            [action[agent] for action in action_profiles if action[agent] != "I"]
            for agent in agents
        ]

    actions_matrix = np.vectorize(process_elem, otypes=[list])(graph)
    agent_actions = [
        np.concatenate([actions[i] for actions in actions_matrix.flat])
        for i in range(len(agents))
    ]
    return {
        f"agent{agent}": np.unique(agent_actions[i]).tolist()
        for i, agent in enumerate(agents)
    }


def read_file(filename):
    """Load and validate an IATL BCGS model from a text file."""
    with open(filename, encoding="utf-8") as handle:
        lines = handle.readlines()

    data = {
        "graph": [],
        "preorder": [],
        "states": [],
        "atomic_propositions": [],
        "matrix_prop": [],
        "initial_state": "",
        "states_counter": 0,
        "atomic_propositions_counter": 0,
        "number_of_agents": 0,
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
    data["preorder"] = np.array(data["preorder"], dtype=int)
    data["agents"] = np.array(list(range(data["number_of_agents"])))
    data["actions"] = get_actions(data["graph"], data["agents"])

    from model_checker.algorithms.explicit.IATL.util.validation import (
        check_conditions_hold,
    )

    check_conditions_hold(data)
    return data
