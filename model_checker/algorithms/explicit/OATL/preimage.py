"""Cost-bounded pre-image computation for OATL."""

from typing import Any, Dict, Set, Tuple

from model_checker.algorithms.explicit.shared.bit_vector import (
    BitVectorStateSet,
    should_use_bit_vectors,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol

_cost_cache: Dict[Tuple[str, str], float] = {}
_base_action_cache: Dict[Tuple[str, tuple], str] = {}


def get_pre_image(cgs, target_states: Set[str]) -> Set[str]:
    """Return state names that have a transition into target_states."""
    target_indices = state_names_to_indices(cgs, target_states)
    graph = cgs.graph
    pre_indices = set()

    for i, row in enumerate(graph):
        for target_idx in target_indices:
            if row[target_idx] != 0:
                pre_indices.add(i)
                break

    return {str(cgs.get_state_name_by_index(idx)) for idx in pre_indices}


def check_if_action_is_extension(action: str, extension_action: str) -> bool:
    """Return True if extension_action is a consistent extension of action."""
    for a, e in zip(action, extension_action):
        if a != "-" and a != e:
            return False
    return True


def get_next_states(cgs, action_profile: str, state_idx: int) -> Set[int]:
    """Return indices of states reachable from state_idx under action_profile."""
    graph = cgs.graph
    reachable = set()
    for next_idx, label in enumerate(graph[state_idx]):
        if label != 0:
            actions = cgs.build_action_list(label)
            for act in actions:
                if act == action_profile or check_if_action_is_extension(
                    action_profile, act
                ):
                    reachable.add(next_idx)
                    break
    return reachable


def _get_cached_base_action(cgs, action: str, agents: Set[str]) -> str:
    """Return base action for (action, agents), using cache when possible."""
    agents_tuple = tuple(sorted(agents))
    cache_key = (action, agents_tuple)
    if cache_key in _base_action_cache:
        return _base_action_cache[cache_key]

    base_action = cgs.get_base_action(action, agents)
    _base_action_cache[cache_key] = base_action
    return base_action


def D(cgs, source_state_name: str, coalition: str, safe_states: Set[str]) -> Set[str]:
    """Actions for coalition from source_state that keep the next state in safe_states."""
    agents = cgs.get_agents_from_coalition(coalition)
    source_idx = cgs.get_index_by_state_name(source_state_name)
    safe_indices = state_names_to_indices(cgs, safe_states)

    graph = cgs.graph
    num_states = len(graph)
    winning_actions = set()

    use_bit_vector = should_use_bit_vectors(num_states)
    if use_bit_vector:
        safe_bits = BitVectorStateSet(num_states, safe_indices)

    all_actions = set()
    for label in graph[source_idx]:
        if label != 0:
            all_actions.update(cgs.build_action_list(label))

    for action in all_actions:
        coalition_move = _get_cached_base_action(cgs, action, agents)
        reachable = get_next_states(cgs, coalition_move, source_idx)
        if reachable:
            if use_bit_vector:
                all_safe = all(idx in safe_bits for idx in reachable)
            else:
                all_safe = reachable.issubset(safe_indices)
            if all_safe:
                winning_actions.add(action)

    return winning_actions


def _cost_to_scalar(costs: Any) -> float:
    """Convert model cost (number or list of numbers) to a single float; lists are summed."""
    if not costs:
        return 0.0
    c0 = costs[0]
    if isinstance(c0, (list, tuple)):
        return sum(c0) if c0 else 0.0
    return float(c0)


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


def calculate_cost(cgs, actions: Set[str], state_name: str) -> float:
    """Return sum of costs for actions from state_name."""
    if not hasattr(cgs, "get_cost_for_action"):
        return 0.0

    total = 0.0
    for action in actions:
        total += _get_cached_cost(cgs, action, state_name)
    return total


def has_affordable_action(
    cgs, actions: Set[str], state_name: str, max_cost: float
) -> bool:
    """Return True if some action has cost <= max_cost; True if model has no cost function."""
    if not hasattr(cgs, "get_cost_for_action"):
        return True

    for action in actions:
        cost = _get_cached_cost(cgs, action, state_name)
        if cost <= max_cost:
            return True
    return False


def min_action_cost(cgs, actions: Set[str], state_name: str) -> float:
    """Return minimum cost over actions from state_name; 0.0 if no cost or empty set."""
    if not hasattr(cgs, "get_cost_for_action") or not actions:
        return 0.0

    min_cost = float("inf")
    for action in actions:
        cost = _get_cached_cost(cgs, action, state_name)
        if cost < min_cost:
            min_cost = cost
    return min_cost if min_cost != float("inf") else 0.0


def cross(
    cgs: CostCGSProtocol,
    max_cost: int,
    coalition: str,
    target_states: Set[str],
    early_stop: Set[str] = None,
) -> Set[str]:
    """Pre-image for OATL: states that can reach target_states in one step within max_cost.

    Args:
        cgs: Cost CGS model.
        max_cost: Maximum cost per step.
        coalition: Coalition string.
        target_states: Target state names.
        early_stop: State names to skip (e.g. already in fixpoint).
    """
    result = set()
    potential_pre = get_pre_image(cgs, target_states)

    for state in potential_pre:
        if early_stop and state in early_stop:
            continue
        actions = D(cgs, state, coalition, target_states)
        if actions and has_affordable_action(cgs, actions, state, max_cost):
            result.add(state)

    return result
