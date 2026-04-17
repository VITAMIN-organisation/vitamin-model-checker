"""Pre-image and strategy/knowledge helpers for CapATL."""

import itertools
from typing import Any, List, Tuple


def find_combinations(lists: List[List[Any]]) -> List[Tuple[Any, ...]]:
    """Cartesian product of the given lists; returns list of tuples."""
    if not lists:
        return []
    return list(itertools.product(*lists))


def get_actions_from_capacity_set(cgs, capacity_set):
    """Return action combinations that satisfy the given capacity set."""

    def get_actions_from_capacity(cgs, cap):
        """Return actions available for capacity cap."""
        ens = cgs.get_action_capacities()
        result = []
        for j in ens:
            if cap in j:
                result.extend(j[1:])  # Actions are after capacity identifier
        return result

    result = []
    a = []
    for elem in capacity_set:
        for cap in elem:
            a.append(get_actions_from_capacity(cgs, cap))
        a = find_combinations(a)
        for x in a:
            if x not in result:
                result.append(x)
        a = []
    return result


def group_by_state(succ_w):
    """Group successor elements by state."""
    interm = []
    states_dict = {}

    for success in succ_w:
        st = success.state
        if st in states_dict:
            states_dict[st].append(success)
        else:
            states_dict[st] = [st, success]
            interm.append(states_dict[st])

    return interm


def action_elem12(elem1, elem2):
    """Return elem2.action if knowledge and state match and actions consistent, else False."""
    know_1 = elem1.knowledge
    know_2 = elem2.knowledge

    st1 = tuple(elem1.state) if not isinstance(elem1.state, tuple) else elem1.state
    st2 = tuple(elem2.state) if not isinstance(elem2.state, tuple) else elem2.state

    if st1 != st2:
        return False

    for j1, j2 in enumerate(know_1):
        for q in j2:
            if q not in know_2[j1]:
                return False
    return elem2.action


def action_in_W2(elem, W):
    """Return list of actions from W consistent with elem."""
    result = []
    for a in W:
        action_result = action_elem12(elem, a)
        if action_result is not False:
            result.append(action_result)
    return result


def intersection_same_q(group_by_elmt, W):
    """Collect actions from W consistent with elements in the group (excluding first)."""
    result = set()
    for elem in group_by_elmt[1:]:
        actions = action_in_W2(elem, W)
        if actions:
            result.update(actions)
    return list(result)


def unique_state_action_couple(succw, W):
    """Return True iff each state in succw has exactly one consistent action in W."""
    group = group_by_state(succw)
    for elem in group:
        if len(intersection_same_q(elem, W)) != 1:
            return False
    return True


def elem_in_W(w, W):
    """Return matching elements in W (knowledge subset and same state), or None."""
    result = []
    for value in W:
        is_subset = True
        val_know = value.knowledge
        w_know = w.knowledge
        for i in range(len(val_know)):
            if not set(val_know[i]).issubset(set(w_know[i])):
                is_subset = False
                break

        if is_subset and value.state == w.state:
            result.append(value)

    return result if result else None


def succ_in_W(succw, W, dict_W):
    """Return True if every element of succw is in dict_W (keyed by (state, knowledge))."""
    if not succw:
        return False

    for elem in succw:
        key = (tuple(elem.state), elem.knowledge)
        if key not in dict_W:
            return False
    return True


def pre(cgs, W, coal_Y):
    """Pre-image for CapATL: elements whose successors are in W with unique state-action and in W."""
    from model_checker.algorithms.explicit.CapATL.utils import (
        Omega_Y,
        succ,
    )

    p_group = []
    omega_Y = Omega_Y(cgs, coal_Y)

    dict_W = {}
    for j in W:
        key = (
            tuple(j.state) if not isinstance(j.state, tuple) else j.state,
            j.knowledge,
        )
        dict_W[key] = j

    for j in omega_Y:
        j_succ = succ(cgs, j)
        if (
            j_succ
            and succ_in_W(j_succ, W, dict_W)
            and unique_state_action_couple(j_succ, W)
        ):
            if j not in p_group:
                p_group.append(j)

    return p_group
