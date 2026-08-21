"""Cost-bounded pre-image computation for OATL."""

from model_checker.algorithms.explicit.shared.cost_utils import cost_to_scalar


def _get_cached_cost(cgs, action: str, state_name: str) -> float:
    """Return cost for (action, state_name), using cache when possible."""
    if not hasattr(cgs, "_oatl_cost_cache"):
        cgs._oatl_cost_cache = {}

    cache_key = (action, state_name)
    if cache_key in cgs._oatl_cost_cache:
        return cgs._oatl_cost_cache[cache_key]

    cost = 0.0
    try:
        costs = cgs.get_cost_for_action(action, state_name)
        cost = cost_to_scalar(costs) if costs else 0.0
    except (KeyError, IndexError, AttributeError, TypeError):
        if "*" in str(action):
            try:
                costs = cgs.get_cost_for_action("*", state_name)
                cost = cost_to_scalar(costs) if costs else 0.0
            except (KeyError, IndexError, AttributeError, TypeError):
                pass

    cgs._oatl_cost_cache[cache_key] = cost
    return cost


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
