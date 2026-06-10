"""Least and greatest fixpoint iteration for set-based model checkers."""

from typing import Callable, Dict, Set, Tuple


def least_fixpoint(initial_set, update_func):
    """Smallest set T such that T = update_func(T)."""
    p = set()
    t = initial_set
    while t != p:
        p = t
        t = update_func(p)
    return p


def least_fixpoint_incremental(initial_set, update_func):
    """Least fixpoint that only processes newly added states each step."""
    result = set(initial_set)
    frontier = set(initial_set)

    while frontier:
        new_states = update_func(result)
        frontier = new_states - result
        result.update(frontier)

    return result


def greatest_fixpoint(initial_set, update_func):
    """Largest set T such that T = update_func(T)."""
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
    """Least fixpoint that also records one predecessor per state for traces."""
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
