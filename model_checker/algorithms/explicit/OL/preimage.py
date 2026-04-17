"""Cost-bounded pre-image computation for OL."""

from typing import List, Set

from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)


def build_pre_set_array(cgs) -> List[Set[int]]:
    """Build per-state list of predecessor state indices."""
    graph = cgs.graph
    n = len(graph)
    pre_sets = [set() for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if graph[i][j] != 0:
                pre_sets[j].add(i)
    return pre_sets


def get_pre_image(pre_sets: List[Set[int]], target_indices: Set[int]) -> Set[int]:
    """Return set of predecessor indices for the given target indices."""
    result = set()
    for idx in target_indices:
        result.update(pre_sets[idx])
    return result


def _edge_cost_to_float(cell: object) -> float:
    """
    Convert a graph cell to a numeric cost for OL.

    OL expects costCGS with Transition_With_Costs: graph cells are 0 or numeric
    (int/float or numeric string). Non-numeric or non-edge cells are treated as 0.
    """
    if cell is None or cell == 0 or cell == "0":
        return 0.0
    if isinstance(cell, (int, float)):
        return float(cell)
    if isinstance(cell, str) and cell != "*":
        try:
            return float(cell)
        except (ValueError, TypeError):
            pass
    return 0.0


def triangle_check(
    cgs, state_idx: int, cost_bound: int, target_indices: Set[int]
) -> bool:
    """Return True if total cost from state_idx to states outside target_indices is <= cost_bound."""
    graph = cgs.graph
    n = len(graph)
    total_cost = 0.0

    for r in range(n):
        if r not in target_indices:
            cell = graph[state_idx][r]
            if cell != 0 and cell != "0":
                total_cost += _edge_cost_to_float(cell)

    return total_cost <= cost_bound


def triangle_down(
    cgs, cost_bound: int, target_states: Set[str], pre_sets: List[Set[int]]
) -> Set[str]:
    """Cost-bounded pre-image: states that can reach target_states within cost_bound."""
    target_indices = state_names_to_indices(cgs, target_states)
    potential_pre = get_pre_image(pre_sets, target_indices)

    winning_indices = set()
    for s_idx in potential_pre:
        if triangle_check(cgs, s_idx, cost_bound, target_indices):
            winning_indices.add(s_idx)

    return {cgs.get_state_name_by_index(idx) for idx in winning_indices}
