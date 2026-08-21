"""Action combination helpers for CapATL (no dependency on utils or pre-image)."""

import itertools
from typing import Any


def find_combinations(lists: list[list[Any]]) -> list[tuple[Any, ...]]:
    """Cartesian product of the given lists; returns list of tuples."""
    if not lists:
        return []
    return list(itertools.product(*lists))


def get_actions_from_capacity_set(cgs, capacity_set):
    """Return flat action labels enabled by any capacity in capacity_set."""

    def get_actions_from_capacity(cgs, cap):
        """Return actions available for capacity cap."""
        ens = cgs.action_capacities
        result = []
        for j in ens:
            if cap in j:
                result.extend(j[1:])
        return result

    result = []
    for elem in capacity_set:
        for cap in elem:
            for action in get_actions_from_capacity(cgs, cap):
                if action not in result:
                    result.append(action)
    return result
