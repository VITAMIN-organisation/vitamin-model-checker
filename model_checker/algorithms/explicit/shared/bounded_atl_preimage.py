"""Pre-image for RBATL and RABATL: a coalition move that lands in the target set and
fits the bound (RABATL: every joint action; RBATL: one), see docs/algorithms/rbatl.md.
"""

from itertools import zip_longest
from typing import Literal

from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions

CostFilter = Literal["rbatl", "rabatl"]
# A coalition move: the destinations of its joint actions and the cost vectors that
# can be charged for it; it is affordable when one of them is within the bound.
Move = tuple[frozenset[int], list[list[int]]]
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
                    cost = _coalition_sum(cost, agents, profile, state)
                move = cgs_actions.process_action_string(profile, agents)
                by_move.setdefault(move, []).append((dest_idx, cost))
        cache[state_idx] = [
            _reduce_move(joint, cost_filter) for joint in by_move.values()
        ]
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


def _within_bound(costs: list[list[int]], bound: list[int]) -> bool:
    """Whether some cost vector is at most bound in each resource the bound covers."""
    return any(
        all(c <= limit for c, limit in zip(cost, bound, strict=False)) for cost in costs
    )


def _reduce_move(
    joint: list[tuple[int, list[int] | None]], cost_filter: CostFilter
) -> Move:
    """RABATL: one vector, the largest per resource, none when a joint action has no
    cost. RBATL: the distinct costs of the joint actions that have one."""
    dests = frozenset(dest for dest, _ in joint)
    costs = [cost for _, cost in joint if cost is not None]
    if cost_filter == "rbatl":
        return dests, [list(c) for c in {tuple(c) for c in costs}]
    if len(costs) < len(joint):
        return dests, []
    return dests, [[max(column) for column in zip_longest(*costs, fillvalue=0)]]


def _coalition_sum(cost, agents: set[int], profile: str, state: str) -> list[int]:
    """The members' costs summed per resource; a flat vector is one resource."""
    rows = cost if cost and isinstance(cost[0], (list, tuple)) else [cost]
    for row in rows:
        short = [i + 1 for i in sorted(agents) if i >= len(row)]
        if short:
            raise ValueError(
                f"[MODEL] Costs_for_actions_split gives {len(row)} cost(s) for "
                f"action {profile} at {state}, but agent {short[0]} is in the coalition"
            )
    return [sum(row[i] for i in agents) for row in rows]


def _profile_cost(cgs: CostCGSProtocol, profile: str, state: str):
    """The model's cost of the joint action at state, None when it has none."""
    try:
        return cgs.get_cost_for_action(profile, state)
    except KeyError:
        return None
