"""Transition cost resolution for costCGS models."""

from typing import Any

from model_checker.algorithms.explicit.shared.coalition_constraints import (
    parse_coalition_and_scalar_constraint,
)


def extract_coalition_and_cost(formula_node_value: str) -> tuple[str, int]:
    """Parse ``<J><n>`` into coalition string and cost bound."""
    coalition, scalar = parse_coalition_and_scalar_constraint(formula_node_value)
    if isinstance(scalar, float) and not scalar.is_integer():
        raise ValueError(
            f"Invalid coalition-cost format '{formula_node_value}': expected integer bound."
        )
    cost = int(scalar)
    if cost < 0:
        raise ValueError(
            f"Invalid coalition-cost format '{formula_node_value}': cost must be non-negative."
        )
    return coalition, cost


def cost_to_scalar(costs: Any) -> float:
    """Convert model cost (number or list of numbers) to a single float."""
    if not costs:
        return 0.0
    if isinstance(costs, (int, float)):
        return float(costs)
    if isinstance(costs, (list, tuple)):
        return float(sum(costs[0] if isinstance(costs[0], (list, tuple)) else costs))
    return float(costs)


def edge_cell_cost(cell: object) -> float:
    """Cost of one `Transition_With_Costs` cell: a number, or one per agent (`1:2:0`) summed."""
    try:
        return float(sum(float(part) for part in str(cell).split(":")))
    except ValueError:
        raise ValueError(
            f"[MODEL] Transition_With_Costs cell '{cell}' is not a cost such as 2 or 1:2:0"
        ) from None
