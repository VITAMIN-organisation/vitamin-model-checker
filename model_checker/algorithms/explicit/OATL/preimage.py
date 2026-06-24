"""Cost-bounded pre-image computation for OATL."""

from typing import Any

_cost_cache: dict[tuple, float] = {}
_base_action_cache: dict[tuple, str] = {}


def _cost_to_scalar(costs: Any) -> float:
    """Convert model cost (number or list of numbers) to a single float; lists are summed."""
    if not costs:
        return 0.0
    first_cost = costs[0]
    if isinstance(first_cost, (list, tuple)):
        return sum(first_cost) if first_cost else 0.0
    return float(first_cost)


def _get_cached_cost(cgs, action: str, state_name: str) -> float:
    """Return cost for (action, state_name), using cache when possible."""
    cache_key = (action, state_name)
    if cache_key in _cost_cache:
        return _cost_cache[cache_key]

    cost = 0.0
    try:
        costs = cgs.get_cost_for_action(action, state_name)
        cost = _cost_to_scalar(costs) if costs else 0.0
    except (KeyError, IndexError, AttributeError, TypeError):
        if "*" in str(action):
            try:
                costs = cgs.get_cost_for_action("*", state_name)
                cost = _cost_to_scalar(costs) if costs else 0.0
            except (KeyError, IndexError, AttributeError, TypeError):
                pass

    _cost_cache[cache_key] = cost
    return cost


def calculate_cost(cgs, actions: set[str], state_name: str) -> float:
    """Return sum of costs for actions from state_name."""
    if not hasattr(cgs, "get_cost_for_action"):
        return 0.0

    total = 0.0
    for action in actions:
        total += _get_cached_cost(cgs, action, state_name)
    return total


def has_affordable_action(
    cgs, actions: set[str], state_name: str, max_cost: float
) -> bool:
    """Return True if some action has cost <= max_cost; True if model has no cost function."""
    if not hasattr(cgs, "get_cost_for_action"):
        return True

    for action in actions:
        cost = _get_cached_cost(cgs, action, state_name)
        if cost <= max_cost:
            return True
    return False


def min_action_cost(cgs, actions: set[str], state_name: str) -> float:
    """Return minimum cost over actions from state_name; 0.0 if no cost or empty set."""
    if not hasattr(cgs, "get_cost_for_action") or not actions:
        return 0.0

    min_cost = float("inf")
    for action in actions:
        cost = _get_cached_cost(cgs, action, state_name)
        if cost < min_cost:
            min_cost = cost
    return min_cost if min_cost != float("inf") else 0.0
