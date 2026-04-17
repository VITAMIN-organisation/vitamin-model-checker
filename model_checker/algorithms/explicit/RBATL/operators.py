"""
RBATL operator handlers for formula tree evaluation.

This module contains handler functions for all RBATL operators, both unary
(NOT, <J><b>X, <J><b>F, <J><b>G) and binary (OR, AND, IMPLIES, <J><b>U).
"""

from model_checker.algorithms.explicit.RBATL.preimage import pre
from model_checker.algorithms.explicit.shared import state_set_to_str
from model_checker.algorithms.explicit.shared.bound_utils import (
    diff_bound,
    extract_coalition_and_bound,
    inc_bound,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.engine.runner import parse_state_set_literal

# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS (NOT in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_globally(cgs, node):
    """Handle <J><b>G operator: coalition can ensure phi forever within resource bounds."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)

    if not any(bound):

        def update(p):
            return pre(cgs, coalition, p, bound) & target_states

        result = greatest_fixpoint(cgs.all_states_set.copy(), update)
        node.value = state_set_to_str(result)
    else:
        p = set()
        curr_bound_p = [0] * len(bound)
        while True:
            remaining_bound = diff_bound(bound, curr_bound_p)
            t = pre(cgs, coalition, target_states, remaining_bound) & target_states
            while t - p:
                p.update(t)
                t = pre(cgs, coalition, p, [0] * len(bound)) & target_states
            if not inc_bound(curr_bound_p, bound):
                break
        node.value = state_set_to_str(p)


def handle_coalition_next(cgs, node):
    """Handle <J><b>X operator: coalition can force next state within resource bounds."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)
    node.value = state_set_to_str(pre(cgs, coalition, target_states, bound))


def handle_coalition_eventually(cgs, node):
    """Handle <J><b>F operator: coalition can eventually reach phi within resource bounds."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)
    all_states = cgs.all_states_set

    if not any(bound):

        def update(p):
            return pre(cgs, coalition, p, bound) & all_states

        result = least_fixpoint(target_states, update)
        node.value = state_set_to_str(result)
    else:
        p = set()
        curr_bound_p = [0] * len(bound)
        while True:
            remaining_bound = diff_bound(bound, curr_bound_p)
            t = pre(cgs, coalition, target_states, remaining_bound) & all_states
            while t - p:
                p.update(t)
                t = pre(cgs, coalition, p, [0] * len(bound)) & all_states
            if not inc_bound(curr_bound_p, bound):
                break
        node.value = state_set_to_str(p)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS (OR, AND, IMPLIES in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_until(cgs, node):
    """Handle <J><b>U operator: coalition can ensure psi eventually while maintaining phi within resource bounds."""
    coalition, bound = extract_coalition_and_bound(node.value)
    states1 = parse_state_set_literal(node.left.value)  # phi states
    states2 = parse_state_set_literal(node.right.value)  # psi states

    if not any(bound):

        def update(p):
            return pre(cgs, coalition, p, bound) & states1

        result = least_fixpoint(states2, update)
        node.value = state_set_to_str(result)
    else:
        p = set()
        curr_bound_p = [0] * len(bound)
        while True:
            remaining_bound = diff_bound(bound, curr_bound_p)
            t = pre(cgs, coalition, states2, remaining_bound) & states1
            while t - p:
                p.update(t)
                t = pre(cgs, coalition, p, [0] * len(bound)) & states1
            if not inc_bound(curr_bound_p, bound):
                break
        node.value = state_set_to_str(p)
