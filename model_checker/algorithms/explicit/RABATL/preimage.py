"""Resource-aware bounded pre-image computation for RABATL."""

from typing import List, Set, Union

from model_checker.algorithms.explicit.shared.bit_vector import (
    BitVectorStateSet,
    should_use_bit_vectors,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol


def get_good_actions(
    cgs: CostCGSProtocol,
    actions: List[str],
    state_idx: int,
    agents: Set[str],
    bound: List[int],
) -> Set[str]:
    """Return actions whose coalition cost is within bound at this state.

    Args:
        cgs: Cost CGS model.
        actions: Available action strings.
        state_idx: Current state index.
        agents: Coalition agent indices (strings).
        bound: Resource bound vector.
    """
    good_actions = set()
    state_name = cgs.get_state_name_by_index(state_idx)

    for action in actions:
        try:
            costs_matrix = cgs.get_cost_for_action(action, state_name)
        except (KeyError, IndexError, AttributeError):
            if "*" in str(action):
                try:
                    costs_matrix = cgs.get_cost_for_action("*", state_name)
                except (KeyError, IndexError, AttributeError):
                    continue
            else:
                continue

        if costs_matrix and not isinstance(costs_matrix[0], (list, tuple)):
            costs_matrix = [costs_matrix]

        is_within_bounds = True
        for resource_idx, agent_costs in enumerate(costs_matrix):
            if resource_idx >= len(bound):
                break

            total_coalition_cost = 0
            for i, cost in enumerate(agent_costs):
                if str(i + 1) in agents:
                    total_coalition_cost += cost

            if total_coalition_cost > bound[resource_idx]:
                is_within_bounds = False
                break

        if is_within_bounds:
            good_actions.add(action)

    return good_actions


def pre(
    cgs: CostCGSProtocol,
    coalition: str,
    state_set: Union[Set[str], str],
    bound: List[int],
) -> Set[str]:
    """Pre-image for RABATL: states from which coalition can force one step into state_set within bound."""
    agents = cgs.get_agents_from_coalition(coalition)
    graph = cgs.graph
    num_states = len(graph)
    target_indices = state_names_to_indices(cgs, state_set)
    pre_states = set()

    use_bit_vector = should_use_bit_vectors(num_states)
    if use_bit_vector:
        target_bits = BitVectorStateSet(num_states, target_indices)

    for source_idx, _row in enumerate(graph):
        actions_to_target = {}
        for target_idx in target_indices:
            if graph[source_idx][target_idx] != 0:
                actions_list = cgs.build_action_list(graph[source_idx][target_idx])
                good_actions = get_good_actions(
                    cgs, actions_list, source_idx, agents, bound
                )
                if good_actions:
                    actions_to_target[target_idx] = good_actions

        if not actions_to_target:
            continue

        all_good_actions = set().union(*actions_to_target.values())

        for action in all_good_actions:
            if "*" in action:
                pre_states.add(source_idx)
                break

            move_profile = cgs.get_coalition_action({action}, agents)
            is_winning = True

            for k, element in enumerate(graph[source_idx]):
                if element == 0:
                    continue

                row_actions = cgs.build_action_list(element)
                opponent_moves = cgs.get_opponent_moves(row_actions, agents)

                if move_profile.intersection(opponent_moves):
                    if use_bit_vector:
                        if k not in target_bits:
                            is_winning = False
                            break
                    else:
                        if k not in target_indices:
                            is_winning = False
                            break

            if is_winning:
                pre_states.add(source_idx)
                break

    return {cgs.get_state_name_by_index(idx) for idx in pre_states}
