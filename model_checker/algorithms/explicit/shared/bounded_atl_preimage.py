"""Shared transition-cache helpers for resource-bounded ATL pre-images."""

from typing import Literal, TypedDict

from model_checker.algorithms.explicit.RABATL.preimage import (
    get_good_actions as rabatl_get_good_actions,
)
from model_checker.algorithms.explicit.RBATL.preimage import (
    get_good_actions as rbatl_get_good_actions,
)
from model_checker.algorithms.explicit.shared.bit_vector import (
    BIT_VECTOR_THRESHOLD,
    BitVectorStateSet,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions

CostFilter = Literal["rbatl", "rabatl"]
TransitionCache = dict[int, "StateTransitionData"]


class StateTransitionData(TypedDict):
    profiles_by_dest: dict[int, list[str]]
    opponent_moves_by_column: list[frozenset]


def build_transition_cache(cgs: CostCGSProtocol, coalition: str) -> TransitionCache:
    """Cache per-state profiles and opponent moves for a fixed coalition."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    cache: TransitionCache = {}

    for state_idx, row in enumerate(cgs.graph):
        profiles_by_dest: dict[int, list[str]] = {}
        opponent_moves_by_column: list[frozenset] = []

        for dest_idx, mask in enumerate(row):
            if mask == 0:
                opponent_moves_by_column.append(frozenset())
                continue

            profiles = cgs.build_action_list(mask)
            profiles_by_dest[dest_idx] = profiles
            opponent_moves_by_column.append(
                frozenset(
                    cgs_actions._process_actions_for_agents(
                        profiles,
                        formatted_agents,
                        num_agents,
                        include_agents=False,
                    )
                )
            )

        cache[state_idx] = {
            "profiles_by_dest": profiles_by_dest,
            "opponent_moves_by_column": opponent_moves_by_column,
        }

    return cache


def _collect_good_actions(
    cgs: CostCGSProtocol,
    source_idx: int,
    target_indices: set[int],
    profiles_by_dest: dict[int, list[str]],
    agents,
    bound: list[int],
    cost_filter: CostFilter,
) -> set[str]:
    """Gather coalition actions that lead toward target_indices within the cost bound."""
    available: set[str] = set()
    for target_idx in target_indices:
        profiles = profiles_by_dest.get(target_idx)
        if not profiles:
            continue
        if cost_filter == "rabatl":
            good = rabatl_get_good_actions(cgs, profiles, source_idx, agents, bound)
        else:
            good = rbatl_get_good_actions(cgs, profiles, source_idx, bound)
        if good:
            available.update(good)
    return available


def _action_forces_all_to_target(
    action: str,
    formatted_agents,
    num_agents: int,
    opponent_moves_by_column: list[frozenset],
    target_indices: set[int],
    target_bits,
    use_bit_vector: bool,
) -> bool:
    """True if every opponent response to action lands inside target_indices."""
    if "*" in action:
        return True

    move_profile = cgs_actions.get_coalition_actions(
        {action}, formatted_agents, num_agents
    )
    for dest_idx, opponent_moves in enumerate(opponent_moves_by_column):
        if not opponent_moves:
            continue
        if not move_profile.intersection(opponent_moves):
            continue
        if use_bit_vector:
            if dest_idx not in target_bits:
                return False
        elif dest_idx not in target_indices:
            return False
    return True


def compute_pre_states(
    cgs: CostCGSProtocol,
    coalition: str,
    state_set: set[str] | str,
    bound: list[int],
    transition_cache: TransitionCache,
    cost_filter: CostFilter,
) -> set[str]:
    """Return state names where coalition can force state_set in one step within bound."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    num_states = len(cgs.graph)
    target_indices = state_names_to_indices(cgs, state_set)

    use_bit_vector = num_states >= BIT_VECTOR_THRESHOLD
    target_bits = (
        BitVectorStateSet(num_states, target_indices) if use_bit_vector else None
    )

    pre_states: set[int] = set()
    for source_idx in range(num_states):
        state_data = transition_cache[source_idx]
        available_actions = _collect_good_actions(
            cgs,
            source_idx,
            target_indices,
            state_data["profiles_by_dest"],
            agents,
            bound,
            cost_filter,
        )
        if not available_actions:
            continue

        opponent_moves_by_column = state_data["opponent_moves_by_column"]
        for action in available_actions:
            if _action_forces_all_to_target(
                action,
                formatted_agents,
                num_agents,
                opponent_moves_by_column,
                target_indices,
                target_bits,
                use_bit_vector,
            ):
                pre_states.add(source_idx)
                break

    return {cgs.get_state_name_by_index(idx) for idx in pre_states}
