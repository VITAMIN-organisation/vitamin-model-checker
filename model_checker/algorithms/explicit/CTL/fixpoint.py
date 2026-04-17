"""
Fixpoint computation helpers for CTL model checking.

Delegates to shared fixpoint_iter with normalization so CTL operators
get normalized state sets. Trace variant from shared.
"""

from typing import Callable, Dict, Set, Tuple

from model_checker.algorithms.explicit.shared import normalize_state_set
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint as _greatest_fixpoint,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    least_fixpoint as _least_fixpoint,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    least_fixpoint_with_trace as _least_fixpoint_with_trace,
)


def _normalized_update(update_func: Callable[[Set[str]], Set[str]]):
    """Wrap update so its result is normalized (for CTL set comparison)."""

    def wrapped(T: Set[str]) -> Set[str]:
        return normalize_state_set(update_func(T))

    return wrapped


def least_fixpoint(
    initial_set: Set[str],
    update_func: Callable[[Set[str]], Set[str]],
) -> Set[str]:
    """Least fixpoint mu Z. update_func(Z), with normalized state sets."""
    return _least_fixpoint(
        normalize_state_set(initial_set), _normalized_update(update_func)
    )


def greatest_fixpoint(
    initial_set: Set[str],
    update_func: Callable[[Set[str]], Set[str]],
) -> Set[str]:
    """Greatest fixpoint nu Z. update_func(Z), with normalized state sets."""
    return _greatest_fixpoint(
        normalize_state_set(initial_set), _normalized_update(update_func)
    )


def least_fixpoint_with_trace(
    initial_set: Set[str],
    update_func_with_trace: Callable[[Set[str]], Tuple[Set[str], Dict[str, str]]],
) -> Tuple[Set[str], Dict[str, str]]:
    """Least fixpoint with predecessor map; uses shared implementation with CTL normalization."""
    return _least_fixpoint_with_trace(
        initial_set,
        update_func_with_trace,
        normalize_state_set_func=normalize_state_set,
    )
