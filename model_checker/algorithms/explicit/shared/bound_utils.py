"""Bound vectors for RBATL and RABATL: parse `<J><b1,b2,...>Op`."""

from model_checker.algorithms.explicit.shared.coalition_constraints import (
    parse_coalition_and_bound_vector,
)


def extract_coalition_and_bound(formula_node_value: str) -> tuple[str, list[int]]:
    """Parse <J><b1,b2,...> into (coalition_str, [b1,b2,...]).

    Raises ValueError with a descriptive message when the format is invalid.
    """
    coalition, bounds = parse_coalition_and_bound_vector(formula_node_value)
    if any(bound < 0 for bound in bounds):
        raise ValueError(
            f"Invalid coalition-bound format '{formula_node_value}': bounds must be non-negative integers."
        )
    return coalition, bounds
