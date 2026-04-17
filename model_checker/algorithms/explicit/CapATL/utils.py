"""
Utility functions for CapATL model checker.

This module provides helper functions for state/index management, capacity
computations, and knowledge set generation.
"""

import functools
import logging

import numpy as np

from model_checker.algorithms.explicit.CapATL.knowledge import (
    p_knowledge,
    p_knowledge_for_Y,
)
from model_checker.algorithms.explicit.CapATL.preimage import (
    find_combinations,
    get_actions_from_capacity_set,
)

logger = logging.getLogger(__name__)


def get_prop_held_in_state(cgs, state):
    """Get atomic propositions that hold in a given state."""
    index = get_index_by_state_name(cgs, state)
    if index is None:
        return None
    prop_matrix = cgs.get_matrix_proposition()
    state_atoms = prop_matrix[index]
    return {prop for prop, value in enumerate(state_atoms) if value == 1}


def get_atom_index(cgs, element):
    """Return the index of the given atom in the array of atomic propositions."""
    array = cgs.get_atomic_prop()
    try:
        index = np.where(array == element)[0][0]
        return index
    except (IndexError, ValueError):
        logger.warning("Atom '%s' not found in model", element)
        return None


def get_index_by_state_name(cgs, state):
    """Get state index from state name with caching."""
    if not hasattr(cgs, "_state_name_to_index_cache"):
        cgs._state_name_to_index_cache = {}
    if isinstance(state, tuple):
        state = "".join(str(elem) for elem in state) if len(state) > 1 else state[0]
    state_str = str(state)

    if state_str in cgs._state_name_to_index_cache:
        return cgs._state_name_to_index_cache[state_str]

    try:
        idx = cgs.get_index_by_state_name(state_str)
        cgs._state_name_to_index_cache[state_str] = idx
        return idx
    except (IndexError, ValueError, AttributeError):
        state_list = cgs.get_states()
        for count, st in enumerate(state_list):
            if state_str == str(st):
                cgs._state_name_to_index_cache[state_str] = count
                return count
        return None


def build_state_cache(cgs):
    """Build state name to index cache."""
    if not hasattr(cgs, "_state_name_to_index_cache"):
        cgs._state_name_to_index_cache = {}
    cgs._state_name_to_index_cache.clear()
    state_list = cgs.get_states()
    for idx, state in enumerate(state_list):
        state_str = str(state)
        cgs._state_name_to_index_cache[state_str] = idx
        if isinstance(state, (tuple, list)) and len(state) > 1:
            cgs._state_name_to_index_cache["".join(str(elem) for elem in state)] = idx


def clear_state_cache(cgs):
    """Clear the state name to index cache."""
    if hasattr(cgs, "_state_name_to_index_cache"):
        cgs._state_name_to_index_cache.clear()


def get_state_name_by_index(cgs, index):
    """Get state name from index."""
    return cgs.get_state_name_by_index(index)


def build_list(cgs, action_string):
    """Converts action_string into a list."""
    if action_string == "*":
        return ["*"] * cgs.get_number_of_agents()
    return action_string.split(",")


def get_agents_from_coalition(coalition):
    """Return a set of agents given a coalition string."""
    return set(coalition.strip("{}").split(","))


def format_agents(agents):
    """Sort and remove 0 from agents."""
    agents_list = sorted([int(a) for a in agents if str(a) != "0"])
    return agents_list


def get_capacities_from_action2(cgs, action, agent):
    """Get capacities for a specific action and agent."""
    cap_ag = cgs.get_capacities_assignment()[int(agent) - 1][1:]
    if action == "*":
        return cap_ag
    result = []
    ens = cgs.get_action_capacities()
    for j in ens:
        if j[0] in cap_ag and action in j:
            result.append(j[0])
    return result


def get_capacities_from_actionvector(cgs, action, agents):
    """Get capacities for an action vector across multiple agents."""
    result1 = []
    for ag in agents:
        ag_idx = int(ag) - 1
        if 0 <= ag_idx < len(action):
            act = action[ag_idx]
            interm = get_capacities_from_action2(cgs, act, ag)
            result1.append(interm)
        else:
            result1.append([])
    return find_combinations(result1)


@functools.lru_cache(maxsize=1)
def X_agt_cap(cgs):
    """Generate all capacity combinations across agents."""
    cap_assgn = cgs.get_capacities_assignment()
    capacity_lists = [elem[1:] for elem in cap_assgn]
    combinations = find_combinations(capacity_lists)
    return [list(value) for value in combinations]


@functools.lru_cache(maxsize=1)
def X_agt_cap2(cgs):
    """Get X_agt_cap as a set of tuples."""
    return {tuple(elem) for elem in X_agt_cap(cgs)}


def possible_knowledge(cgs):
    """Generate all possible knowledge sets."""
    cap_assgn = cgs.get_capacities_assignment()
    agent_possible_caps = []
    for elem in cap_assgn:
        agent_caps = elem[1:]
        agent_possible_caps.append([(c,) for c in agent_caps])

    return find_combinations(agent_possible_caps)


def pointed_knowledge_set(cgs):
    """Generate all possible state-knowledge pairs."""
    pk_set = []
    states = cgs.get_states()
    poss_k = possible_knowledge(cgs)
    n_agents = cgs.get_number_of_agents()
    agents_tot = list(range(1, n_agents + 1))

    for state in states:
        for know in poss_k:
            pk_set.append(p_knowledge(state, know, agents_tot))
    return pk_set


@functools.lru_cache(maxsize=8192)
def Omega_Y(cgs, coalition_Y):
    """Compute possible knowledge elements for a specific coalition."""
    agents_y = get_agents_from_coalition(coalition_Y)
    pk_set = pointed_knowledge_set(cgs)

    omega_y_res = []
    for pk in pk_set:
        agents_y_actions = []
        for ag in sorted(agents_y):
            ag_idx = int(ag) - 1
            ag_know = pk.knowledge[ag_idx]
            actions = get_actions_from_capacity_set(cgs, [ag_know])
            agents_y_actions.append(actions)

        joint_actions = find_combinations(agents_y_actions)
        for beta in joint_actions:
            omega_y_res.append(
                p_knowledge_for_Y(
                    pk.state,
                    pk.knowledge,
                    beta,
                    coalition_Y,
                    list(range(1, cgs.get_number_of_agents() + 1)),
                )
            )

    return omega_y_res


def pi_omega_Y(cgs, W, coalition_Y):
    """Extract winning elements that belong to Omega_Y."""
    omega_Y = Omega_Y(cgs, coalition_Y)
    dict_W = {}
    for obj in W:
        dict_W[
            (
                tuple(obj.state) if not isinstance(obj.state, tuple) else obj.state,
                obj.knowledge,
            )
        ] = obj

    res = []
    for val in omega_Y:
        st = tuple(val.state) if not isinstance(val.state, tuple) else val.state
        if (st, val.knowledge) in dict_W:
            res.append(val)
    return res


def pi_theta(cgs, W):
    """Filter pointed knowledge set to elements with actions in W."""
    theta = pointed_knowledge_set(cgs)
    winning_states = {
        (
            tuple(obj.state) if not isinstance(obj.state, tuple) else obj.state,
            obj.knowledge,
        )
        for obj in W
    }
    return [
        elem
        for elem in theta
        if (
            tuple(elem.state) if not isinstance(elem.state, tuple) else elem.state,
            elem.knowledge,
        )
        in winning_states
    ]


@functools.lru_cache(maxsize=1024)
def indistinguishable_action(cgs, state1, state2, action, agent):
    """Epistemic indistinguishable action check."""
    graph = cgs.graph
    idx1 = get_index_by_state_name(cgs, state1)
    idx2 = get_index_by_state_name(cgs, state2)
    if idx1 is None or idx2 is None:
        return None

    actions_encoded = graph[idx1][idx2]
    if actions_encoded == 0:
        return None

    possible_actions = build_list(cgs, actions_encoded)
    ag_idx = int(agent) - 1

    return [
        act
        for act in possible_actions
        if ag_idx < len(act) and ag_idx < len(action) and act[ag_idx] == action[ag_idx]
    ]


@functools.lru_cache(maxsize=1024)
def function_F_for_succ(cgs, q1, q2, alpha, agent_a):
    """Successor knowledge update function."""
    possible_actions = indistinguishable_action(cgs, q1, q2, alpha, agent_a)
    if possible_actions is None:
        return None

    n_agents = cgs.get_number_of_agents()
    agents_tot = list(range(1, n_agents + 1))

    res = []
    for act in possible_actions:
        res.extend(get_capacities_from_actionvector(cgs, act, agents_tot))
    return res


@functools.lru_cache(maxsize=8192)
def succ(cgs, pk_for_Y):
    """Compute successor knowledge elements given a coalition joint action."""
    coal = pk_for_Y.coalition
    agents_coal = format_agents(get_agents_from_coalition(coal))
    action = pk_for_Y.action
    state = pk_for_Y.state
    set_capacity = pk_for_Y.knowledge
    graph = cgs.graph
    n_agents = cgs.get_number_of_agents()
    agents_tot = list(range(1, n_agents + 1))

    idx = get_index_by_state_name(cgs, state)
    if idx is None:
        return []

    successors = []
    for succ_idx, actions_encoded in enumerate(graph[idx]):
        if actions_encoded == 0:
            continue

        succ_name = get_state_name_by_index(cgs, succ_idx)
        possible_actions = build_list(cgs, actions_encoded)

        for alpha in possible_actions:
            # Check if alpha is consistent with coalition's beta
            is_consistent = True
            for i, ag_num in enumerate(agents_coal):
                ag_idx = ag_num - 1
                if (
                    ag_idx >= len(alpha)
                    or i >= len(action)
                    or str(alpha[ag_idx]) != str(action[i])
                ):
                    is_consistent = False
                    break
            if not is_consistent:
                continue

            new_know_list = []
            for agent in agents_tot:
                succ_caps = function_F_for_succ(cgs, state, succ_name, alpha, agent)
                if succ_caps is None:
                    new_know_list.append([])
                    continue
                # Current knowledge & New info
                new_know = set(set_capacity[agent - 1]) & set(succ_caps)
                new_know_list.append(list(new_know))

            new_know_tuple = tuple(tuple(k) for k in new_know_list)
            successors.append(p_knowledge(succ_name, new_know_tuple, agents_tot))

    return successors


def verify_digits_and_letters(s):
    """Check if string contains both digits and letters (e.g. '1c')."""
    s = str(s)
    has_digit = any(c.isdigit() for c in s)
    has_alpha = any(c.isalpha() for c in s)
    return has_digit and has_alpha
