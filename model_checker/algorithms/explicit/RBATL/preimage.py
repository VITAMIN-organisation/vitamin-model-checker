"""Resource-bounded pre-image computation for RBATL."""

from model_checker.parsers.game_structures.cgs import CostCGSProtocol


def _costs_within_bound(costs: list[int], bound: list[int]) -> bool:
    """Check cost_i <= bound[i]; stop when the bound vector runs out."""
    for resource_idx, cost in enumerate(costs):
        if resource_idx >= len(bound):
            break
        if cost > bound[resource_idx]:
            return False
    return True


def get_good_actions(
    cgs: CostCGSProtocol, actions: list[str], state_idx: int, bound: list[int]
) -> set[str]:
    """Return actions at state_idx whose cost fits within bound."""
    good_actions: set[str] = set()
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

        if _costs_within_bound(costs, bound):
            good_actions.add(action)
    return good_actions
