"""Coalition-sum cost pre-image helpers for COTL."""

from model_checker.algorithms.explicit.shared.oatl_index_preimage import cross_indices
from model_checker.parsers.game_structures.cgs import cgs_actions


def get_cached_coalition_cost(cgs, action, state, agents_set):
    """Return coalition-summed cost for (action, state, agents_set), using per-cgs cache."""
    if not hasattr(cgs, "_cost_cache"):
        cgs._cost_cache = {}
    key = (action, state, tuple(agents_set))
    if key in cgs._cost_cache:
        return cgs._cost_cache[key]
    try:
        costs = cgs.get_cost_for_action(action, state)
        if isinstance(costs[0], list):
            aux = sum(costs[0][int(i) - 1] for i in agents_set)
        else:
            aux = sum(costs[int(i) - 1] for i in agents_set)
    except (KeyError, IndexError, AttributeError, TypeError):
        aux = None
    cgs._cost_cache[key] = aux
    return aux


def min_coalition_action_cost(cgs, action_set, state, coalition, agents_set=None):
    """Minimum coalition-summed cost among actions in action_set at state."""
    if agents_set is None:
        agents_set = cgs_actions.get_agents_from_coalition(coalition)
    minimum = None
    for action in action_set:
        cost = get_cached_coalition_cost(cgs, action, state, agents_set)
        if cost is None:
            continue
        if minimum is None or cost < minimum:
            minimum = cost
    return minimum


def cross_index(
    cgs,
    max_cost,
    coalition,
    state_indices,
    solve_context,
    agents_set,
    base_action_cache,
):
    """Cost-bounded pre-image in index space using coalition-summed costs."""

    def affordable(cgs_inner, actions, state_name, bound):
        cost = min_coalition_action_cost(
            cgs_inner, actions, state_name, coalition, agents_set=agents_set
        )
        return cost is not None and cost <= bound

    return cross_indices(
        cgs,
        max_cost,
        coalition,
        state_indices,
        solve_context,
        base_action_cache,
        affordable,
    )
