"""Pre-image for RBATL and RABATL: a coalition move whose every joint action lands
in the target set and costs at most the bound."""

from typing import Any, Literal

from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions

CostFilter = Literal["rbatl", "rabatl"]
# Per state: coalition move -> [(destination index, the joint action's cost or None)].
TransitionCache = dict[int, dict[str, list[tuple[int, Any]]]]


def build_transition_cache(cgs: CostCGSProtocol, coalition: str) -> TransitionCache:
    """Each state's joint actions grouped by the coalition's part of them, with the
    model's cost of each joint action (None when the model gives none)."""
    agents = cgs_actions.format_agents(cgs_actions.get_agents_from_coalition(coalition))
    num_agents = cgs.get_number_of_agents()
    cache: TransitionCache = {}
    for state_idx, row in enumerate(cgs.graph):
        state = cgs.get_state_name_by_index(state_idx)
        by_move: dict[str, list[tuple[int, Any]]] = {}
        for dest_idx, mask in enumerate(row):
            if mask == 0 or mask == "0":
                continue
            for profile in cgs.build_action_list(mask):
                (move,) = cgs_actions.get_coalition_actions(
                    {profile}, agents, num_agents
                )
                by_move.setdefault(move, []).append(
                    (dest_idx, _profile_cost(cgs, profile, state))
                )
        cache[state_idx] = by_move
    return cache


def compute_pre_states(
    cgs: CostCGSProtocol,
    coalition: str,
    state_set: set[str] | str,
    bound: list[int],
    transition_cache: TransitionCache,
    cost_filter: CostFilter,
) -> set[str]:
    """States with a coalition move whose joint actions all reach state_set within bound."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    target = state_names_to_indices(cgs, state_set)
    pre_states: set[int] = set()
    for state_idx, by_move in transition_cache.items():
        for transitions in by_move.values():
            if all(
                dest in target and _within_bound(costs, agents, bound, cost_filter)
                for dest, costs in transitions
            ):
                pre_states.add(state_idx)
                break
    return state_indices_to_names(cgs, pre_states)


def _within_bound(
    costs: Any, agents: set[str], bound: list[int], cost_filter: CostFilter
) -> bool:
    """Whether a joint action's cost is at most bound in each resource the bound
    covers; a joint action with no cost (None) never is."""
    if costs is None:
        return False
    if cost_filter == "rabatl":
        if costs and not isinstance(costs[0], (list, tuple)):
            costs = [costs]
        costs = [
            sum(cost for i, cost in enumerate(per_agent) if str(i + 1) in agents)
            for per_agent in costs
        ]
    return all(cost <= limit for cost, limit in zip(costs, bound, strict=False))


def _profile_cost(cgs: CostCGSProtocol, profile: str, state: str) -> Any:
    """The model's cost of the joint action at state, falling back to the `*` cost
    for a wildcard action; None when the model has neither."""
    for key in (profile, "*") if "*" in profile else (profile,):
        try:
            return cgs.get_cost_for_action(key, state)
        except (KeyError, IndexError, AttributeError):
            continue
    return None
