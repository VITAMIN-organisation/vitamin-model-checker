"""Least and greatest fixpoint iteration for set-based model checkers."""


def _iterate_fixpoint(previous, current, update_func):
    """Iterate until ``current`` stabilizes under ``update_func``."""
    while current != previous:
        previous = current
        current = update_func(previous)
    return current


def least_fixpoint(initial_set, update_func):
    """Smallest set T such that T = update_func(T)."""
    return _iterate_fixpoint(set(), initial_set, update_func)


def greatest_fixpoint(initial_set, update_func):
    """Largest set T such that T = update_func(T)."""
    return _iterate_fixpoint(initial_set, update_func(initial_set), update_func)
