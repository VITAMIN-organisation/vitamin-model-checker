"""
OL operator handlers for formula tree evaluation.

This module contains handler functions for all OL operators, both unary
(NOT, <Jn>X, <Jn>F, <Jn>G) and binary (OR, AND, IMPLIES, <Jn>U).
"""

from typing import List, Set

from model_checker.algorithms.explicit.OL.preimage import triangle_down
from model_checker.algorithms.explicit.shared import state_set_to_str
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.engine.runner import parse_state_set_literal


def extract_bound(formula_node_value: str) -> int:
    """Extract cost bound from operator: <Jn>."""
    try:
        bound = (
            int(formula_node_value[2:-1])
            if formula_node_value.endswith(">")
            else int(formula_node_value[2:])
        )
    except (ValueError, IndexError):
        bound = 0
    return bound


# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS (NOT is in shared.boolean_operators; solver imports it)
# ---------------------------------------------------------


def handle_demonic_globally(cgs, node, pre_sets: List[Set[int]]):
    """Handle <Jn>G operator: demonic globally within cost bound."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)

    def update(p):
        return target & triangle_down(cgs, bound, p, pre_sets)

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = state_set_to_str(result)


def handle_demonic_next(cgs, node, pre_sets: List[Set[int]]):
    """Handle <Jn>X operator: demonic next within cost bound."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = state_set_to_str(triangle_down(cgs, bound, target, pre_sets))


def handle_demonic_eventually(cgs, node, pre_sets: List[Set[int]]):
    """Handle <Jn>F operator: demonic eventually within cost bound."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)
    all_states = cgs.all_states_set

    def update(p):
        return target | (all_states & triangle_down(cgs, bound, p, pre_sets))

    result = least_fixpoint(target, update)
    node.value = state_set_to_str(result)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS (OR, AND, IMPLIES in shared.boolean_operators)
# ---------------------------------------------------------


def handle_demonic_until(cgs, node, pre_sets: List[Set[int]]):
    """Handle <Jn>U operator: demonic until within cost bound."""
    bound = extract_bound(node.value)
    states1 = parse_state_set_literal(node.left.value)  # phi states
    states2 = parse_state_set_literal(node.right.value)  # psi states

    def update(p):
        return states2 | (states1 & triangle_down(cgs, bound, p, pre_sets))

    result = least_fixpoint(states2, update)
    node.value = state_set_to_str(result)
