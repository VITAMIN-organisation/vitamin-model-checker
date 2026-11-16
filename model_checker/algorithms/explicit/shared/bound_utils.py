"""Bound vectors for RBATL and RABATL: parse `<J><b1,b2,...>Op`."""

from model_checker.algorithms.explicit.shared.coalition_constraints import (
    parse_coalition_and_bound_vector,
)


def extract_coalition_and_bound(formula_node_value: str, cgs) -> tuple[str, list[int]]:
    """Parse <J><b1,b2,...> into (coalition_str, [b1,b2,...]) for the model `cgs`.

    Raises ValueError with a descriptive message when the format is invalid.
    """
    coalition, bounds = parse_coalition_and_bound_vector(formula_node_value)
    if any(bound < 0 for bound in bounds):
        raise ValueError(
            f"Invalid coalition-bound format '{formula_node_value}': bounds must be non-negative integers."
        )
    # A cost is one vector (RBATL) or one row per resource (RABATL).
    resources = max(map(len, cgs.cost_for_action.values()), default=0)
    if resources and len(bounds) > resources:
        raise ValueError(
            f"[VALIDATION] Bound {bounds} has {len(bounds)} values, but the "
            f"model's costs have {resources} resource(s)."
        )
    return coalition, bounds
