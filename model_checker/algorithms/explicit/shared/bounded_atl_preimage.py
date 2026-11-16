"""Pre-image for RBATL and RABATL: a coalition move whose every joint action lands
in the target set and costs at most the bound."""

from itertools import zip_longest
from typing import Literal

from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions

CostFilter = Literal["rbatl", "rabatl"]
# A coalition move: the destinations of its joint actions and the largest cost among
# them per resource, None when a joint action has no cost in the model.
Move = tuple[frozenset[int], list[int] | None]
TransitionCache = dict[int, list[Move]]


def build_transition_cache(
    cgs: CostCGSProtocol, coalition: str, cost_filter: CostFilter
) -> TransitionCache:
    """Each state's coalition moves; RABATL sums the members' costs per resource."""
    agents = cgs_actions.format_agents(cgs_actions.get_agents_from_coalition(coalition))
    cache: TransitionCache = {}
    for state_idx, row in enumerate(cgs.graph):
        state = cgs.get_state_name_by_index(state_idx)
        by_move: dict[str, list[tuple[int, list[int] | None]]] = {}
        for dest_idx, mask in enumerate(row):
            if mask == 0 or mask == "0":
                continue
            for profile in cgs.build_action_list(mask):
                cost = _profile_cost(cgs, profile, state)
                if cost is not None and cost_filter == "rabatl":
                    cost = _coalition_sum(cost, agents)
                move = cgs_actions.process_action_string(profile, agents)
                by_move.setdefault(move, []).append((dest_idx, cost))
        cache[state_idx] = [_reduce_move(joint) for joint in by_move.values()]
    return cache


def compute_pre_states(
    cgs: CostCGSProtocol,
    state_set: set[str] | str,
    bound: list[int],
    transition_cache: TransitionCache,
) -> set[str]:
    """States with a coalition move whose joint actions all reach state_set within bound."""
    target = state_names_to_indices(cgs, state_set)
    pre_states = {
        state_idx
        for state_idx, moves in transition_cache.items()
        if any(dests <= target and _within_bound(cost, bound) for dests, cost in moves)
    }
    return state_indices_to_names(cgs, pre_states)


def _within_bound(cost: list[int] | None, bound: list[int]) -> bool:
    """Whether a cost is at most bound in each resource the bound covers."""
    return cost is not None and all(
        c <= limit for c, limit in zip(cost, bound, strict=False)
    )


def _reduce_move(joint: list[tuple[int, list[int] | None]]) -> Move:
    dests = frozenset(dest for dest, _ in joint)
    costs = [cost for _, cost in joint if cost is not None]
    if len(costs) < len(joint):
        return dests, None
    return dests, [max(column) for column in zip_longest(*costs, fillvalue=0)]


def _coalition_sum(cost, agents: set[int]) -> list[int]:
    """The members' costs summed per resource; a flat vector is one resource."""
    rows = cost if cost and isinstance(cost[0], (list, tuple)) else [cost]
    return [sum(row[i] for i in agents) for row in rows]


def _profile_cost(cgs: CostCGSProtocol, profile: str, state: str):
    """The model's cost of the joint action at state, None when it has none."""
    try:
        return cgs.get_cost_for_action(profile, state)
    except KeyError:
        return None
