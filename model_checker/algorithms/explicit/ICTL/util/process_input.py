import time

import numpy as np
from tqdm import tqdm


# Check whether the model is a square matrix as required
def check_is_squared(model):
    return model.shape[0] == model.shape[1]


# The relation transition has to be serial
def check_is_transition_serial(model):
    return np.logical_and.reduce(["R" in row or "P,R" in row for row in model])


# the preorder relation has to be reflective
def check_is_preorder_reflective(model):
    return all(element in ["P", "P,R"] for element in np.diagonal(model))


# the preorder relation has to be antisymmetric
def check_is_preorder_antisymmetric(model):
    return all(
        not (
            ("P" in model[i, j] or "P,R" in model[i, j])
            and ("P" in model[j, i] or "P,R" in model[j, i])
        )
        for i in range(model.shape[0])
        for j in range(model.shape[1])
        if i != j
    )


def check_is_preorder_transitive(model):
    n = model.shape[0]
    for i in range(n):
        for j in range(n):
            # se (i->j) è "P" o "P,R"
            if model[i, j] in ["P", "P,R"]:
                for k in range(n):
                    # se (j->k) è "P" o "P,R", ma (i->k) non lo è => violazione
                    if model[j, k] in ["P", "P,R"]:
                        if model[i, k] not in ["P", "P,R"]:
                            return False
    return True


# Birelational model must respect 3 constraint and this is a mask to call the control to check whether these
# conditions hold
def check_has_condition(model, row_indices, col_indices, row_condition, col_condition):
    return all(
        any(
            not all(
                model[row_idx, col_idx] in col_condition
                and model[col_idx, row_idx] in row_condition
                for col_idx in col_indices
            )
            for row_idx in row_indices
            if any(model[row_idx, col_idx] in row_condition for col_idx in col_indices)
        )
        for col_idx in col_indices
        if any(model[row_idx, col_idx] in col_condition for row_idx in row_indices)
    )


# if xRy and yRz => xPu and uRz
def check_has_c1(model):
    return check_has_condition(
        model, range(model.shape[0]), range(model.shape[0]), ["R", "P,R"], ["P", "P,R"]
    )


# if xRy and xRz => yPu and zRu
def check_has_c2(model):
    return check_has_condition(
        model, range(model.shape[0]), range(model.shape[0]), ["R", "P,R"], ["P", "P,R"]
    )


# if xPy and yRz => xRu and uPz
def check_has_c3(model):
    return check_has_condition(
        model, range(model.shape[0]), range(model.shape[0]), ["P", "P,R"], ["R", "P,R"]
    )


# returns the index, given a state name
def get_index_by_state_name(states_list, state):
    index = np.where(states_list == state)[0][0]
    return index


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
        if element not in ["0", "P"]
    ]


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
        if element in ["P,R", "P"]
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


def read_file(filename):
    with open(filename) as f:
        lines = f.readlines()

    data = {
        "graph": [],
        "states": [],
        "atomic_propositions": [],
        "matrix_prop": [],
        "initial_state": "",
        "states_counter": 0,
        "atomic_propositions_counter": 0,
    }

    section_actions = {
        "Transition": lambda line: handle_transition(line, data),
        "Name_State": lambda line: handle_name_state(line, data),
        "Initial_State": lambda line: handle_initial_state(line, data),
        "Atomic_propositions": lambda line: handle_atomic_propositions(line, data),
        "Labelling": lambda line: handle_labelling(line, data),
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
    check_conditions_hold(data)
    return data


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


# The model is a Birelational frame, so it has to satisfy these condition to apply the model checking algorithm on it
def check_conditions_hold(data):
    try:
        # check whether the read model satisfies all conditions
        assert check_is_squared(data["graph"]), "The graph is not squared."
        assert check_is_transition_serial(
            data["graph"]
        ), "The graph does not satisfy transition serial condition."
        assert check_is_preorder_reflective(
            data["graph"]
        ), "The graph is not reflective."
        assert check_is_preorder_antisymmetric(
            data["graph"]
        ), "The graph is not antisymmetric."
        assert check_is_preorder_transitive(
            data["graph"]
        ), "The graph is not transitive."
        assert check_has_c1(data["graph"]), "The graph does not satisfy condition C1."
        assert check_has_c2(data["graph"]), "The graph does not satisfy condition C2."
        assert check_has_c3(data["graph"]), "The graph does not satisfy condition C3."
        assert data["states_counter"] > 0, "There's no states in your model."
        assert (
            data["atomic_propositions_counter"] > 0
        ), "There's no atoms in your model."
        assert np.all(
            np.isin(data["matrix_prop"], [0, 1])
        ), "Only boolean proposition matrix are admitted."
        preorder_pairs = get_preorder_edges(data["graph"], data["states"])
        preorder = get_preorder_no_reflective(preorder_pairs)
        assert check_labeling_preorder(preorder, data["matrix_prop"], data["states"]), (
            "Labeling function not respected " "for preorder."
        )

    except AssertionError as e:
        raise e

    except Exception as e:
        raise e


def get_atom_index(element, atomic_propositions):
    try:
        index = np.where(atomic_propositions == element)[0][0]
        return index
    except IndexError:
        pass  # Element not found in array.
        return None


# returns the state, given an index
def get_state_name_by_index(states_list, index):
    return states_list[index]


def get_label(index):
    return f"s{index}"


def calculate_subset_states_hat(stati, closures, subset_states):
    """
    Calcola l'insieme Y^ dato l'insieme S, le upward closure e l'insieme Y.

    Parameters:
    stati (set): L'insieme degli stati del modello
    closures (dict): Dizionario dove le chiavi sono gli elements di S e i valori sono le loro upward closure
    subset_states (set): Sottoinsieme di S

    Returns:
    set: L'insieme Y^
    """
    return {s for s in stati if closures[s].issubset(subset_states)}


# this method doesn't generate every possible correct model but just the ones that we are really sure
# that satisfy every condition and that are useful to represent the information gaining:
# the matrix identity has a P relation to guarantee reflexivity
# every (i,i+1) until i < n_states - 1 has an R relation to guarantee the seriality
def generate_experiment_model(states_row, states_col):
    if states_col <= 2 or states_row <= 1:
        raise ValueError("Matrix dimensions too small. Minimum supported size is 2x3.")

    data = {
        "graph": [],
        "states": [],
        "atomic_propositions": [],
        "matrix_prop": [],
        "initial_state": "",
        "states_counter": 0,
        "atomic_propositions_counter": 0,
    }

    n_states = states_row * states_col
    data["graph"] = generate_graph(n_states, states_row, states_col)
    data["states"] = np.array([f"s{i}" for i in range(n_states)])
    data["states_counter"] = n_states
    data["initial_state"] = data["states"][0]
    (
        data["matrix_prop"],
        data["atomic_propositions"],
        data["atomic_propositions_counter"],
    ) = generate_labeling_matrix(n_states, states_col)
    check_conditions_hold(data)
    return data


def generate_graph(n_states, states_row, states_col):
    relations = generate_square_matrix_reflective(n_states)
    create_zigzag_structure(n_states, relations, states_col)
    guarantee_seriality(n_states, relations, states_col)
    return guarantee_antisymmetry_transitivity(
        n_states, states_row, states_col, relations
    )


def guarantee_antisymmetry_transitivity(n_states, states_row, states_col, relations):
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
    return relations


def guarantee_seriality(n_states, relations, states_col):
    # To guarantee seriality we put random relations on lower triangular matrix
    j_indices = [
        np.arange(i, i + states_col - 1) for i in range(0, n_states - states_col + 1)
    ]
    n_extractions = np.random.choice(np.arange(1, states_col))
    i_indices = np.tile(np.arange(states_col - 1, n_states), n_extractions)
    extracted = np.array(
        [[np.random.choice(j) for j in j_indices] for _ in range(n_extractions)]
    ).flatten()
    relations[i_indices, extracted] = "R"


def create_zigzag_structure(n_states, relations, states_col):
    # Zigzag structure, we have n_cols states connected with classic transition relation and the last one is connected
    # to the next one with the preorder
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


def generate_square_matrix_reflective(n_states):
    # Squared matrix
    relations = np.full((n_states, n_states), "0", dtype=object)
    # Reflexivity
    diagonal_values = np.random.choice(["P", "P,R"], size=n_states)
    np.fill_diagonal(relations, diagonal_values)
    return relations


def generate_labeling_matrix(n_states, states_col):
    atomic_propositions = np.array(["e", "h", "c"])
    proposition_matrix = np.full((n_states, atomic_propositions.shape[0]), 0)

    # create indices for all states except the first one
    indices = np.arange(1, n_states)

    # find indices that satisfy the conditions
    cond1 = indices % states_col == 0
    cond2 = indices % states_col == states_col - 1
    cond3 = ~(cond1 | cond2)  # neither first nor last column

    # set the propositions based on the conditions
    proposition_matrix[indices[cond1], 1] = 1
    proposition_matrix[indices[cond2], 1] = 1
    proposition_matrix[indices[cond3], 0] = 1

    return proposition_matrix, atomic_propositions, len(atomic_propositions)


def do_test_generator(states_row_max, states_col_max):
    for i in range(2, states_row_max):
        for j in range(3, states_col_max):
            time.time()
            generate_experiment_model(i, j)
            time.time()


def generate(states_row, states_col):
    time.time()
    generate_experiment_model(states_row, states_col)
    time.time()


# --------------------------- Generation of the experiment 3k model ---------------------------


def generate3k_square_matrix_reflective(k):
    # Squared matrix
    relations = np.full((k * 3, k * 3), "0", dtype=object)
    # Reflexivity
    diagonal_values = np.tile(["P,R", "P", "P,R"], k)
    np.fill_diagonal(relations, diagonal_values)
    return relations


def create_3k_structure(k, reflective_relations):
    for i in range(0, k):
        offset = 3 * (i - 1)
        if k > 1 and offset > 0:
            reflective_relations[offset][offset + 3] = "P"
            reflective_relations[offset + 1][offset + 4] = "P"
            reflective_relations[offset + 2][offset + 5] = "P"
        reflective_relations[offset][offset + 1] = reflective_relations[offset + 1][
            offset + 2
        ] = "R"


def guarantee_3k_transitivity(k, relations):
    indices = [np.arange(i, 3 * k, 3) for i in range(3)]
    i_index, j_index = zip(
        *[(i, j) for arr in indices for i in arr for j in arr if i < j]
    )
    relations[i_index, j_index] = "P"
    return relations


def generate_3kgraph(k):
    relations = generate3k_square_matrix_reflective(k)
    create_3k_structure(k, relations)
    if k > 1:
        guarantee_3k_transitivity(k, relations)
    return relations


def merge_3k_graphs(n):
    """
    Genera i modelli 3k (k=1...n) e fonde le relative matrici di transizione
    in un'unica grande matrice (NumPy array) di dimensione sum_{k=1}^n 3k.

    Ritorna: np.array di stringhe (dtype=object).
    """

    # 1. Genero i dizionari d_k usando la funzione generate_3k_model(k)
    matrices = [generate_3kgraph(k) for k in range(1, n + 1)]

    # Ognuna è un array NumPy di dimensione 3k x 3k

    # 2. Calcolo la dimensione di ogni matrice e la dimensione totale
    dims = [m.shape[0] for m in matrices]  # es: [3, 6, 9, ...] se n=3
    tot_dim = sum(dims)  # dimensione totale

    # 3. Inizializzo la matrice grande NxN con stringhe '0'
    big_matrix = np.full((tot_dim, tot_dim), "0", dtype=object)

    # 4. Copio ogni matrice nel blocco corrispondente (in diagonale)
    offsets = []
    offset = 0
    for mat in matrices:
        sz = mat.shape[0]
        big_matrix[offset : offset + sz, offset : offset + sz] = mat
        offsets.append(offset)
        offset += sz

    # 5. Aggiungo le 'P' per preservare la transitività rispetto all'inference step
    j_index = np.array([o - 1 for o in offsets[1:]])
    indexes = []
    for i in range(len(j_index) - 1):
        x = j_index[i]
        y = j_index[i + 1]
        rows = range(x + 3, y, 3)
        # Per ognuno di questi, la colonna è x
        for r in rows:
            indexes.append((r, x))

    for r, c in indexes:
        big_matrix[r, c] = "P"

    return np.array(big_matrix), dims


def generate3k_labeling_matrix(data, n, dims):
    matrix_proposition = np.zeros(
        (data["states_counter"], data["atomic_propositions_counter"])
    )

    # Labeling states with pk
    counts = np.arange(1, n + 1)
    total_ones = counts.sum()
    col_ind = np.repeat(np.arange(n), counts)
    row_ind = np.arange(0, 3 * total_ones, 3)
    matrix_proposition[row_ind, col_ind] = 1

    # Labeling states with an
    states_an = list(range(2, data["states_counter"], 3))
    repetitions = []
    for i in range(1, n + 1):
        repetitions.extend(range(1, i + 1))
    for i in range(len(states_an)):
        for j in range(repetitions[i]):
            matrix_proposition[states_an[i]][j + n] = 1

    # Labeling states with Yes and Know
    offset = 0
    for i in dims:
        matrix_proposition[i - 1 + offset, -1] = 1
        matrix_proposition[i - 1 + offset, -2] = 1
        matrix_proposition[i - 4 + offset, -2] = 1
        offset += i

    return matrix_proposition


def generate_3n_model(n):
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
    data["matrix_prop"] = generate3k_labeling_matrix(data, n, dims)
    # check_conditions_hold(data)
    return data
