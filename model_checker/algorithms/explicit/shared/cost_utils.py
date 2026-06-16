"""Transition cost resolution for costCGS models."""

from typing import Any, Optional, Tuple

from model_checker.algorithms.explicit.shared.coalition_constraints import (
    parse_coalition_and_scalar_constraint,
)


def extract_coalition_and_cost(formula_node_value: str) -> Tuple[str, int]:
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


def numeric_cell_cost(cell: object) -> Optional[float]:
    """Return cost when the cell is numeric (Transition_With_Costs); else None."""
    if cell is None or cell in (0, "0"):
        return 0.0
    if isinstance(cell, (int, float)):
        return float(cell)
    if isinstance(cell, str) and cell != "*":
        try:
            return float(cell)
        except (ValueError, TypeError):
            return None
    return None


def _lookup_action_cost(cgs, action: str, state_name: str) -> Optional[float]:
    """Return transition cost for action at state, or None when lookup fails."""
    try:
        costs = cgs.get_cost_for_action(action, state_name)
        return cost_to_scalar(costs) if costs else 0.0
    except (KeyError, IndexError, AttributeError, TypeError):
        return None


def transition_cell_cost(cgs, state_idx: int, cell: object) -> float:
    """Return the cost of one outgoing transition cell from state_idx."""
    numeric_cost = numeric_cell_cost(cell)
    if numeric_cost is not None:
        return numeric_cost

    if not hasattr(cgs, "get_cost_for_action"):
        return 0.0

    state_name = cgs.get_state_name_by_index(state_idx)
    action = str(cell)
    cost = _lookup_action_cost(cgs, action, state_name)
    if cost is not None:
        return cost
    if "*" in action:
        return _lookup_action_cost(cgs, "*", state_name) or 0.0
    return 0.0
