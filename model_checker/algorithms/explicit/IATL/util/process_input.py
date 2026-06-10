import sys

import numpy as np
from tqdm import tqdm


# Checks whether the model is a square matrix as required
def check_is_squared(model):
    return model.shape[0] == model.shape[1]


def check_the_model_does_not_contains_zero_elements(model):
    return np.all(np.any(model != 0, axis=1))


# Checks whether in every state, any agent has an available action (Idle or not)
def check_agent_action(model, n):
    return all(
        all(len(s) % n == 0 for s in str(elem).split(","))
        for row in model
        for elem in row
        if elem != 0
    )


def check_idle_action(model, n):
    return all(model[i][i] == (("I" * n + ",") * n)[:-1] for i in range(len(model)))


def check_is_preorder_reflective(model):
    return np.all(np.diagonal(model) == 1)


# the preorder relation has to be antisymmetric
def check_is_preorder_antisymmetric(model):
    return all(
        not ((model[i, j] == 1) and (model[j, i] == 1))
        for i in range(model.shape[0])
        for j in range(model.shape[1])
        if i != j
    )


def check_is_preorder_transitive(model):
    n = model.shape[0]
    return all(
        model[i, k] == 1
        for i in range(n)
        for j in range(n)
        for k in range(n)
        if model[i, j] == 1 and model[j, k] == 1
    )


# returns the index, given a state name
def get_index_by_state_name(states_list, state):
    return np.where(states_list == state)[0][0]


# if for each state s,s', if sPs' => V(s) is a subset of V(s')
def check_labeling_preorder(preorder_dict, mat_proposition, states_list):
    return all(
        all(
            mat_proposition[get_index_by_state_name(states_list, state)][i] == 1
            and mat_proposition[get_index_by_state_name(states_list, greater_state)][i]
            == 1
            for i in range(len(mat_proposition[0]))
            if mat_proposition[get_index_by_state_name(states_list, state)][i] == 1
        )
        for state in preorder_dict
        for greater_state in preorder_dict[state]
    )


# returns the preorder edges of a graph
def get_preorder_edges(relations, states_list):
    return [
        (
            (states_list[i], states_list[i])
            if element == "*"
            else (states_list[i], states_list[j])
        )
        for i, row in enumerate(relations)
        for j, element in enumerate(row)
        if element == 1
    ]


# returns the edges of a graph
def get_edges(relations, states_list):
    return [
        (
            (states_list[i], states_list[i])
            if element == "*"
            else (states_list[i], states_list[j])
        )
        for i, row in enumerate(relations)
        for j, element in enumerate(row)
        if element not in ["0"]
    ]


def get_atomic_propositions_for_states(states, propositions, labelling_matrix):
    """
    This function returns the atomic propositions that are true (correspond to "1")
    for the specified states in the labelling matrix.

    Parameters:
    - propositions: List of atomic propositions (e.g., ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']).
    - labelling_matrix: 2D list where each row corresponds to a state and each column to an atomic proposition.
    - states: List of states for which to find the corresponding atomic propositions (e.g., ['s0']).

    Returns:
    - Dictionary where keys are the states and values are lists of atomic propositions that are true for those states.
    """

    # Map state names to their corresponding indices (assuming 's0' corresponds to index 0, 's1' to index 1, and so on)
    state_indices = {f"s{i}": i for i in range(len(labelling_matrix))}

    return {
        state: [
            propositions[i]
            for i, val in enumerate(labelling_matrix[state_indices[state]])
            if val == 1
        ]
        for state in states
    }


def get_atomic_propositions_for_state(
    state, propositions, labelling_matrix, states_list
):
    index = get_index_by_state_name(state, states_list)
    return {
        state: [
            propositions[i] for i, val in enumerate(labelling_matrix[index]) if val == 1
        ]
    }


def get_unique_values_from_dict_values(dictionary):
    """
    This function takes a dictionary as input and returns a list of unique values from the dictionary values.

    Parameters:
    - dictionary: A dictionary where the keys are state names and the values are lists of atomic propositions.

    Returns:
    - A list of unique atomic propositions from the dictionary values.
    """
    return list({prop for props in dictionary.values() for prop in props})


def get_reachable_states(transitions, init_state):
    from collections import defaultdict, deque

    # Crea un defaultdict che mappa ogni stato agli stati che può raggiungere
    transition_dict = defaultdict(list)
    for src, dest in transitions:
        transition_dict[src].append(dest)

    # Inizializza la coda per BFS e il set di stati visitati
    queue = deque([init_state])
    reachable_states = {init_state}

    # BFS per trovare tutti gli stati raggiungibili
    while queue:
        state = queue.popleft()
        next_states = [
            next_state
            for next_state in transition_dict[state]
            if next_state not in reachable_states
        ]
        queue.extend(next_states)
        reachable_states.update(next_states)
    return reachable_states


# It returns a dictionary where keys are the states and every value is a set where the elements are the states
# greater than the state key in respect of the preorder
def get_preorder(preorder_pairs, n_states):
    upward = np.zeros((n_states, n_states))
    indices = np.array(
        [(int(pair[0][1:]), int(pair[1][1:])) for pair in preorder_pairs]
    )
    upward[indices[:, 0], indices[:, 1]] = 1
    return {
        f"s{a}": {f"s{b}" for b in range(n_states) if upward[a, b] == 1}
        for a in tqdm(range(n_states))
    }


# It returns the preorder with no reflective pairs
def get_preorder_no_reflective(preorder_pairs):
    return {
        a: {b for _, b in preorder_pairs if a == _ and a != b}
        for a, _ in preorder_pairs
        if {b for _, b in preorder_pairs if a == _ and a != b}
    }


# The model is a BCGS, so it has to satisfy these condition to apply the model checking algorithm on it
def check_conditions_hold(data):
    try:
        # check whether the read model satisfies all conditions
        assert check_is_squared(data["graph"]), "The graph is not squared."
        assert check_agent_action(data["graph"], data["number_of_agents"]), (
            "Some agents doesn't have available " "actions in some states."
        )
        assert check_the_model_does_not_contains_zero_elements(
            data["graph"]
        ), "zero outer edges from a state"
        assert check_idle_action(data["graph"], data["number_of_agents"]), (
            "There's no Idle from some states " "and some agents"
        )
        assert np.all(
            np.isin(data["preorder"], [0, 1])
        ), "Only boolean proposition matrix are admitted."
        assert check_is_preorder_reflective(
            data["preorder"]
        ), "The preorder is not reflective."
        assert check_is_preorder_antisymmetric(
            data["preorder"]
        ), "The preorder is not antisymmetric."
        assert check_is_preorder_transitive(
            data["preorder"]
        ), "The preorder is not transitive."
        assert data["states_counter"] > 0, "There's no states in your model."
        assert (
            data["atomic_propositions_counter"] > 0
        ), "There's no atoms in your model."
        assert data["number_of_agents"] > 0, "There's no actions in your model."
        assert np.all(
            np.isin(data["matrix_prop"], [0, 1])
        ), "Only boolean proposition matrix are admitted."
        preorder_pairs = get_preorder_edges(data["preorder"], data["states"])
        preorder = get_preorder_no_reflective(preorder_pairs)
        assert check_labeling_preorder(preorder, data["matrix_prop"], data["states"]), (
            "Labeling function not " "respected for" " preorder."
        )

    except AssertionError:
        sys.exit(1)

    except Exception:
        sys.exit(1)


def get_actions(graph, agents):
    def process_elem(elem):
        if elem == 0 or elem == "*":
            return [[], []]
        actions = elem.split(",")
        return [
            [action[agent] for action in actions if action[agent] != "I"]
            for agent in agents
        ]

    actions_matrix = np.vectorize(process_elem, otypes=[list])(graph)
    agent_actions = [
        np.concatenate([actions[i] for actions in actions_matrix.flat])
        for i in range(len(agents))
    ]
    actions_per_agent = {
        f"agent{agent}": np.unique(agent_actions[i]).tolist()
        for i, agent in enumerate(agents)
    }
    return actions_per_agent


# returns a set of agents given a coalition (e.g. 1,2,3)
def get_agents_from_coalition(coalition):
    return set(coalition.split(","))


def handle_transition(line, data):
    values = line.split()
    data["graph"].append(values)


def handle_name_state(line, data):
    values = line.split()
    data["states"].extend(values)


def handle_initial_state(line, data):
    data["initial_state"] = line


def handle_atomic_propositions(line, data):
    values = line.split()
    data["atomic_propositions"].extend(values)


def handle_labelling(line, data):
    values = line.split()
    data["matrix_prop"].append(values)


def handle_preorder(line, data):
    values = line.split()
    data["preorder"].append(values)


def handle_number_agents(line, data):
    data["number_of_agents"] = int(line)


def read_file(filename):
    with open(filename) as f:
        lines = f.readlines()

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

    section_actions = {
        "Transition": lambda line: handle_transition(line, data),
        "Preorder": lambda line: handle_preorder(line, data),
        "Name_State": lambda line: handle_name_state(line, data),
        "Initial_State": lambda line: handle_initial_state(line, data),
        "Atomic_propositions": lambda line: handle_atomic_propositions(line, data),
        "Labelling": lambda line: handle_labelling(line, data),
        "Number_of_agents": lambda line: handle_number_agents(line, data),
    }

    current_section = None
    for file_line in lines:
        file_line = file_line.strip()
        if file_line in section_actions:
            current_section = file_line
        elif current_section:
            section_actions[current_section](file_line)

    data["states_counter"] = len(data["states"])
    data["atomic_propositions_counter"] = len(data["atomic_propositions"])
    data["graph"] = np.array(data["graph"])
    data["states"] = np.array(data["states"])
    data["atomic_propositions"] = np.array(data["atomic_propositions"])
    data["matrix_prop"] = np.array(data["matrix_prop"], dtype=int)
    data["preorder"] = np.array(data["preorder"], dtype=int)
    data["agents"] = np.array(list(range(data["number_of_agents"])))
    data["actions"] = get_actions(data["graph"], data["agents"])
    check_conditions_hold(data)
    return data
