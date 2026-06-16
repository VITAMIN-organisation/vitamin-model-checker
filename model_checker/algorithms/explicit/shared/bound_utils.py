"""
Bound vector utilities for resource-bounded logics (RABATL, RBATL).

Parses <J><b1,b2,...>Op and provides lexicographic increment/difference for bound vectors.
"""

from typing import List, Tuple

from model_checker.algorithms.explicit.shared.coalition_constraints import (
    parse_coalition_and_bound_vector,
)


def inc_bound(current_bound: List[int], max_bound: List[int]) -> bool:
    """Increment current_bound lexicographically; return False when past max_bound."""
    for i in range(len(current_bound)):
        if max_bound[i] == 0:
            current_bound[i] = 0
            continue
        current_bound[i] += 1
        if current_bound[i] <= max_bound[i]:
            return True
        current_bound[i] = 0
    return False


def extract_coalition_and_bound(formula_node_value: str) -> Tuple[str, List[int]]:
    """Parse <J><b1,b2,...> into (coalition_str, [b1,b2,...]).

    Raises ValueError with a descriptive message when the format is invalid.
    """
    coalition, bounds = parse_coalition_and_bound_vector(formula_node_value)
    if any(bound < 0 for bound in bounds):
        raise ValueError(
            f"Invalid coalition-bound format '{formula_node_value}': bounds must be non-negative integers."
        )
    return coalition, bounds
