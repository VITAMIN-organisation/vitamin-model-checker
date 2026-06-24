"""Resource-aware bounded pre-image computation for RABATL."""

from model_checker.parsers.game_structures.cgs import CostCGSProtocol


def get_good_actions(
    cgs: CostCGSProtocol,
    actions: list[str],
    state_idx: int,
    agents: set[str],
    bound: list[int],
) -> set[str]:
    """Return actions at state_idx whose coalition cost fits within bound."""
    good_actions: set[str] = set()
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
