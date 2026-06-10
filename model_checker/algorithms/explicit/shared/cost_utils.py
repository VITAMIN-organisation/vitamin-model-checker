"""Transition cost resolution for costCGS models."""

from typing import Any, Optional, Tuple


def extract_coalition_and_cost(formula_node_value: str) -> Tuple[str, int]:
    """Parse ``<J><n>`` into coalition string and cost bound."""
    parts = formula_node_value[1:].split(">")
    return parts[0], int(parts[1][1:])


def cost_to_scalar(costs: Any) -> float:
    """Convert model cost (number or list of numbers) to a single float."""
    if not costs:
        return 0.0
    if isinstance(costs, (int, float)):
        return float(costs)
    if isinstance(costs, (list, tuple)):
        if not costs:
            return 0.0
        first = costs[0]
        if isinstance(first, (list, tuple)):
            return float(sum(first)) if first else 0.0
        return float(sum(costs))
    return float(costs)


def numeric_cell_cost(cell: object) -> Optional[float]:
    """Return cost when the cell is numeric (Transition_With_Costs); else None."""
    if cell is None or cell == 0 or cell == "0":
        return 0.0
    if isinstance(cell, (int, float)):
        return float(cell)
    if isinstance(cell, str) and cell != "*":
        try:
            return float(cell)
        except (ValueError, TypeError):
            return None
    return None


def transition_cell_cost(cgs, state_idx: int, cell: object) -> float:
    """Return the cost of one outgoing transition cell from state_idx."""
    numeric_cost = numeric_cell_cost(cell)
    if numeric_cost is not None:
        return numeric_cost
    if cell in (0, "0"):
        return 0.0

    if not hasattr(cgs, "get_cost_for_action"):
        return 0.0

    state_name = cgs.get_state_name_by_index(state_idx)
    action = str(cell)
    try:
        costs = cgs.get_cost_for_action(action, state_name)
        return cost_to_scalar(costs) if costs else 0.0
    except (KeyError, IndexError, AttributeError, TypeError):
        if "*" in action:
            try:
                costs = cgs.get_cost_for_action("*", state_name)
                return cost_to_scalar(costs) if costs else 0.0
            except (KeyError, IndexError, AttributeError, TypeError):
                pass
    return 0.0
