"""Action combination helpers for CapATL (no dependency on utils or pre-image)."""

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
                result.extend(j[1:])
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
