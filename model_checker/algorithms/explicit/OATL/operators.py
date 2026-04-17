"""
OATL operator handlers for formula tree evaluation.

This module contains handler functions for all OATL operators, both unary
(NOT, <Jn>X, <Jn>F, <Jn>G) and binary (OR, AND, IMPLIES, <Jn>U).
"""

from typing import Tuple

from model_checker.algorithms.explicit.OATL.preimage import (
    D,
    cross,
    get_pre_image,
    has_affordable_action,
    min_action_cost,
)
from model_checker.algorithms.explicit.shared import state_set_to_str
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.engine.runner import parse_state_set_literal


def extract_coalition_and_cost(formula_node_value: str) -> Tuple[str, int]:
    """Extract coalition and cost from operator: <Jn>Op."""
    parts = formula_node_value[1:].split(">")
    coalition = parts[0]
    cost = int(parts[1][1:])
    return coalition, cost


# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS (NOT in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_globally(cgs, node):
    """Handle <Jn>G operator: coalition can ensure phi forever within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    target = parse_state_set_literal(node.left.value)

    def update(p):
        return target & cross(cgs, n, coalition, p)

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = state_set_to_str(result)


def handle_coalition_next(cgs, node):
    """Handle <Jn>X operator: coalition can force next state within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = state_set_to_str(cross(cgs, n, coalition, target))


def handle_coalition_eventually(cgs, node):
    """Handle <Jn>F operator: coalition can eventually reach phi within cost bound."""
    coalition, max_cost = extract_coalition_and_cost(node.value)
    target = parse_state_set_literal(node.left.value)

    all_states = {str(s) for s in cgs.all_states_set}
    target_str = {str(s) for s in target}
    min_cost_to_reach = {state: float("inf") for state in all_states}
    for state in target_str:
        min_cost_to_reach[state] = 0

    result = set(target_str)
    frontier = set(target_str)

    while frontier:
        potential_pre = get_pre_image(cgs, result)
        candidates = potential_pre - result

        new_states = set()
        for state in candidates:
            state_str = str(state)
            current_min = min_cost_to_reach.get(state_str, float("inf"))
            if current_min != float("inf") and current_min > max_cost:
                continue

            actions = D(cgs, state_str, coalition, result)
            if not actions:
                continue

            affordable = has_affordable_action(cgs, actions, state_str, max_cost)
            if not affordable:
                continue

            action_cost = min_action_cost(cgs, actions, state_str)
            if action_cost < min_cost_to_reach[state_str]:
                min_cost_to_reach[state_str] = action_cost
            new_states.add(state_str)

        frontier = new_states
        result.update(frontier)

    node.value = state_set_to_str(result)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS (OR, AND, IMPLIES in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_until(cgs, node):
    """Handle <Jn>U operator: coalition can ensure psi eventually while maintaining phi within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update_with_skip(p):
        return p | (states1 & cross(cgs, n, coalition, p, early_stop=p))

    result = least_fixpoint(states2, update_with_skip)
    node.value = state_set_to_str(result)
