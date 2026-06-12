"""Index-space pre-image helpers shared by OATL (aligned with COTL)."""

from typing import Any, Dict, List, Set

from model_checker.algorithms.explicit.shared.bit_vector import (
    BIT_VECTOR_THRESHOLD,
    BitVectorStateSet,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions

SolveContext = Dict[str, Any]


def build_pre_by_index(graph) -> List[Set[int]]:
    """Build target index -> set of source indices from the graph."""
    num_states = len(graph)
    pre_by_index = [set() for _ in range(num_states)]
    for src in range(num_states):
        for tgt in range(num_states):
            if graph[src][tgt] != 0 and graph[src][tgt] != "0":
                pre_by_index[tgt].add(src)
    return pre_by_index


def pre_indices(state_set_index: Set[int], pre_by_index: List[Set[int]]) -> Set[int]:
    """Return predecessor state indices in one step."""
    result: Set[int] = set()
    for target_idx in state_set_index:
        result.update(pre_by_index[target_idx])
    return result


def check_if_action_is_extension(action: str, extension_action: str) -> bool:
    """Return True if extension_action is a consistent extension of action."""
    for coalition_char, extension_char in zip(action, extension_action):
        if coalition_char != "-" and coalition_char != extension_char:
            return False
    return True


def next_states(cgs, action_profile: str, state_idx: int, graph=None) -> Set[int]:
    """Return indices reachable from state_idx when the coalition plays action_profile."""
    outgoing = cgs.graph[state_idx] if graph is None else graph[state_idx]
    reachable: Set[int] = set()
    for next_idx, label in enumerate(outgoing):
        if label == 0 or label == "0":
            continue
        for act in cgs.build_action_list(label):
            if act == action_profile or check_if_action_is_extension(
                action_profile, act
            ):
                reachable.add(next_idx)
                break
    return reachable


def get_cached_base_action(cgs, action: str, agents_set: Set[str], cache: Dict) -> str:
    """Return base coalition action for (action, agents_set), using cache when possible."""
    key = (action, tuple(sorted(agents_set)))
    if key not in cache:
        cache[key] = cgs_actions.get_coalition_actions(
            {action},
            cgs_actions.format_agents(agents_set),
            cgs.get_number_of_agents(),
        ).pop()
    return cache[key]


def dominant_action_indices(
    cgs,
    source_idx: int,
    safe_indices: Set[int],
    agents_set: Set[str],
    graph,
    base_action_cache: Dict,
) -> Set[str]:
    """Return dominant coalition actions that keep the next state in safe_indices."""
    num_states = len(graph)
    use_bit_vector = num_states >= BIT_VECTOR_THRESHOLD
    if use_bit_vector:
        safe_bits = BitVectorStateSet(num_states, safe_indices)
    else:
        unsafe_indices = set(range(num_states)) - safe_indices

    winning_actions: Set[str] = set()
    for _dest_idx, cell in enumerate(graph[source_idx]):
        if cell == 0 or cell == "0":
            continue
        for action in cgs.build_action_list(cell):
            coalition_move = get_cached_base_action(
                cgs, action, agents_set, base_action_cache
            )
            reachable = next_states(cgs, coalition_move, source_idx, graph)
            if not reachable:
                continue
            if use_bit_vector:
                all_safe = all(idx in safe_bits for idx in reachable)
            else:
                all_safe = len(reachable & unsafe_indices) == 0
            if all_safe:
                winning_actions.add(action)
    return winning_actions


def cross_indices(
    cgs: CostCGSProtocol,
    max_cost: int,
    coalition: str,
    target_indices: Set[int],
    solve_context: SolveContext,
    base_action_cache: Dict,
    has_affordable_action_fn,
) -> Set[int]:
    """Cost-bounded pre-image in index space."""
    graph = solve_context["graph"]
    pre_by_index = solve_context["pre_by_index"]
    agents_set = cgs_actions.get_agents_from_coalition(coalition)
    candidate_sources = pre_indices(target_indices, pre_by_index)
    result: Set[int] = set()

    for source_idx in candidate_sources:
        actions = dominant_action_indices(
            cgs,
            source_idx,
            target_indices,
            agents_set,
            graph,
            base_action_cache,
        )
        if not actions:
            continue
        state_name = cgs.get_state_name_by_index(source_idx)
        if has_affordable_action_fn(cgs, actions, state_name, max_cost):
            result.add(source_idx)

    return result


def cross_state_names(
    cgs: CostCGSProtocol,
    max_cost: int,
    coalition: str,
    target_states: Set[str],
    solve_context: SolveContext,
    base_action_cache: Dict,
    has_affordable_action_fn,
    early_stop: Set[str] = None,
) -> Set[str]:
    """State-name wrapper around index-space cost-bounded pre-image."""
    target_indices = state_names_to_indices(cgs, target_states)
    pre_state_indices = cross_indices(
        cgs,
        max_cost,
        coalition,
        target_indices,
        solve_context,
        base_action_cache,
        has_affordable_action_fn,
    )
    result = {cgs.get_state_name_by_index(idx) for idx in pre_state_indices}
    if early_stop is not None:
        early_stop_str = {str(state) for state in early_stop}
        result = {state for state in result if state not in early_stop_str}
    return result
