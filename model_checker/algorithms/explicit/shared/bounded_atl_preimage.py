"""Shared transition-cache helpers for resource-bounded ATL pre-images."""

from typing import Dict, List, Literal, Set, TypedDict, Union

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
TransitionCache = Dict[int, "StateTransitionData"]


class StateTransitionData(TypedDict):
    profiles_by_dest: Dict[int, List[str]]
    opponent_moves_by_column: List[frozenset]


def build_transition_cache(cgs: CostCGSProtocol, coalition: str) -> TransitionCache:
    """Cache per-state profiles and opponent moves for a fixed coalition."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    graph = cgs.graph
    cache: TransitionCache = {}

    for state_idx, row in enumerate(graph):
        profiles_by_dest: Dict[int, List[str]] = {}
        opponent_moves_by_column: List[frozenset] = []

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


def compute_pre_states(
    cgs: CostCGSProtocol,
    coalition: str,
    state_set: Union[Set[str], str],
    bound: List[int],
    transition_cache: TransitionCache,
    cost_filter: CostFilter,
) -> Set[str]:
    """Return state names where coalition can force state_set in one step within bound."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    graph = cgs.graph
    num_states = len(graph)
    target_indices = state_names_to_indices(cgs, state_set)
    pre_states: Set[int] = set()

    use_bit_vector = num_states >= BIT_VECTOR_THRESHOLD
    if use_bit_vector:
        target_bits = BitVectorStateSet(num_states, target_indices)

    for source_idx in range(num_states):
        state_data = transition_cache[source_idx]
        profiles_by_dest = state_data["profiles_by_dest"]
        opponent_moves_by_column = state_data["opponent_moves_by_column"]

        available_actions: Set[str] = set()
        for target_idx in target_indices:
            profiles = profiles_by_dest.get(target_idx)
            if not profiles:
                continue
            if cost_filter == "rabatl":
                good_actions = rabatl_get_good_actions(
                    cgs, profiles, source_idx, agents, bound
                )
            else:
                good_actions = rbatl_get_good_actions(cgs, profiles, source_idx, bound)
            if good_actions:
                available_actions.update(good_actions)

        if not available_actions:
            continue

        for action in available_actions:
            if "*" in action:
                pre_states.add(source_idx)
                break

            move_profile = cgs_actions.get_coalition_actions(
                {action}, formatted_agents, num_agents
            )
            is_winning = True

            for dest_idx, opponent_moves in enumerate(opponent_moves_by_column):
                if not opponent_moves:
                    continue

                if move_profile.intersection(opponent_moves):
                    if use_bit_vector:
                        if dest_idx not in target_bits:
                            is_winning = False
                            break
                    elif dest_idx not in target_indices:
                        is_winning = False
                        break

            if is_winning:
                pre_states.add(source_idx)
                break

    return {cgs.get_state_name_by_index(idx) for idx in pre_states}
