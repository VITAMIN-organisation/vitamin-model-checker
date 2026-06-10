"""Resource-bounded pre-image computation for RBATL."""

from typing import List, Set, Union

from model_checker.algorithms.explicit.shared.bit_vector import (
    BIT_VECTOR_THRESHOLD,
    BitVectorStateSet,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CostCGSProtocol, cgs_actions


def get_good_actions(
    cgs: CostCGSProtocol, actions: List[str], state_idx: int, bound: List[int]
) -> Set[str]:
    """Return actions at state_idx whose cost fits within bound."""
    good_actions = set()
    state_name = cgs.get_state_name_by_index(state_idx)
    for action in actions:
        try:
            costs = cgs.get_cost_for_action(action, state_name)
        except (KeyError, IndexError, AttributeError):
            if "*" in str(action):
                try:
                    costs = cgs.get_cost_for_action("*", state_name)
                except (KeyError, IndexError, AttributeError):
                    continue
            else:
                continue

        if all(c <= b for c, b in zip(costs, bound)):
            good_actions.add(action)
    return good_actions


def pre(
    cgs: CostCGSProtocol,
    coalition: str,
    state_set: Union[Set[str], str],
    bound: List[int],
) -> Set[str]:
    """States where coalition can move into state_set in one step within bound."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    graph = cgs.graph
    num_states = len(graph)
    target_indices = state_names_to_indices(cgs, state_set)
    pre_states = set()

    use_bit_vector = num_states >= BIT_VECTOR_THRESHOLD
    if use_bit_vector:
        target_bits = BitVectorStateSet(num_states, target_indices)

    dict_state_action = {}

    for i, _row in enumerate(graph):
        for j in target_indices:
            if graph[i][j] != 0:
                actions_list = cgs.build_action_list(graph[i][j])
                good_actions = get_good_actions(cgs, actions_list, i, bound)
                if good_actions:
                    dict_state_action[(i, j)] = good_actions

    for source_idx in range(num_states):
        available_actions = set()
        for target_idx in target_indices:
            if (source_idx, target_idx) in dict_state_action:
                available_actions.update(dict_state_action[(source_idx, target_idx)])

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
            for k, element in enumerate(graph[source_idx]):
                if element == 0:
                    continue

                row_actions = cgs.build_action_list(element)
                opponent_moves = cgs_actions._process_actions_for_agents(
                    row_actions, formatted_agents, num_agents, include_agents=False
                )

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
