"""Least and greatest fixpoint iteration for set-based model checkers."""

from typing import Callable, Dict, Set, Tuple


def _iterate_fixpoint(previous, current, update_func):
    """Iterate until ``current`` stabilizes under ``update_func``."""
    while current != previous:
        previous = current
        current = update_func(previous)
    return current


def least_fixpoint(initial_set, update_func):
    """Smallest set T such that T = update_func(T)."""
    return _iterate_fixpoint(set(), initial_set, update_func)


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
    return _iterate_fixpoint(initial_set, update_func(initial_set), update_func)


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
