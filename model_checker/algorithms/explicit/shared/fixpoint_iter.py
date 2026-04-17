"""
Fixpoint iteration for logics that use T := update(T) until T stabilizes.

Used by ATL, CTL, OATL, OL, RABATL, RBATL, COTL. For least: start from initial,
iterate T := update(T). For greatest: start from initial, iterate until fixpoint.
"""

from typing import Callable, Dict, Set, Tuple


def least_fixpoint(initial_set, update_func):
    """Least fixpoint mu Z. update_func(Z)."""
    p = set()
    t = initial_set
    while t != p:
        p = t
        t = update_func(p)
    return p


def least_fixpoint_incremental(initial_set, update_func):
    """
    Incremental least fixpoint: mu Z. update_func(Z)

    Optimized version that tracks only newly discovered states (frontier)
    to reduce redundant set operations. The update_func still receives the
    full accumulated set, but we track which states are new each iteration.

    This can be faster when update_func is expensive and many states
    converge early.
    """
    result = set(initial_set)
    frontier = set(initial_set)

    while frontier:
        new_states = update_func(result)
        frontier = new_states - result
        result.update(frontier)

    return result


def greatest_fixpoint(initial_set, update_func):
    """Greatest fixpoint nu Z. update_func(Z)."""
    p = initial_set
    t = update_func(p)
    while t != p:
        p = t
        t = update_func(p)
    return p


def least_fixpoint_with_trace(
    initial_set: Set[str],
    update_func_with_trace: Callable[[Set[str]], Tuple[Set[str], Dict[str, str]]],
    normalize_state_set_func=None,
) -> Tuple[Set[str], Dict[str, str]]:
    """Least fixpoint with predecessor map for trace building.

    update_func_with_trace(T) returns (new_T, predecessors_map). Predecessors
    are merged across iterations (first occurrence kept).
    """
    T = (
        normalize_state_set_func(set(initial_set))
        if normalize_state_set_func
        else set(initial_set)
    )
    complete_predecessors: Dict[str, str] = {}

    while True:
        new_T, new_predecessors = update_func_with_trace(T)
        if normalize_state_set_func:
            new_T = normalize_state_set_func(new_T)

        for state, pred in new_predecessors.items():
            if state not in complete_predecessors:
                complete_predecessors[state] = pred

        if new_T == T:
            break
        T = new_T

    return T, complete_predecessors
