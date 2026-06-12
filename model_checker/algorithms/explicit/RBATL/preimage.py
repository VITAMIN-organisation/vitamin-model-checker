"""Resource-bounded pre-image computation for RBATL."""

from typing import List, Set

from model_checker.parsers.game_structures.cgs import CostCGSProtocol


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

        if all(cost <= resource_bound for cost, resource_bound in zip(costs, bound)):
            good_actions.add(action)
    return good_actions
