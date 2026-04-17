"""
ATL operator handlers for formula tree evaluation.

This module contains handler functions for all ATL operators, both unary
(NOT, <A>X, <A>F, <A>G) and binary (OR, AND, IMPLIES, <A>U).
"""

from model_checker.algorithms.explicit.ATL.preimage import pre
from model_checker.algorithms.explicit.shared import state_set_to_str
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.engine.runner import parse_state_set_literal

# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS (NOT in shared.boolean_operators; solver imports it)
# ---------------------------------------------------------


def handle_coalition_globally(cgs, node, transition_cache):
    """Handle <A>G operator: coalition can ensure phi forever."""
    coalition = node.value[1:-2]
    states = parse_state_set_literal(node.left.value)

    def update(p):
        return pre(cgs, coalition, p, transition_cache) & states

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = state_set_to_str(result)


def handle_coalition_next(cgs, node, transition_cache):
    """Handle <A>X operator: coalition can force next state to satisfy phi."""
    coalition = node.value[1:-2]
    states = parse_state_set_literal(node.left.value)
    node.value = state_set_to_str(pre(cgs, coalition, states, transition_cache))


def handle_coalition_eventually(cgs, node, transition_cache):
    """Handle <A>F operator: coalition can eventually reach phi."""
    coalition = node.value[1:-2]
    states = parse_state_set_literal(node.left.value)

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        return p | pre(cgs, coalition, p, transition_cache, early_stop=p_indices)

    result = least_fixpoint(states, update_with_skip)
    node.value = state_set_to_str(result)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS (OR, AND, IMPLIES in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_until(cgs, node, transition_cache):
    """Handle <A>U operator: coalition can ensure psi eventually while maintaining phi."""
    coalition = node.value[1:-2]
    states1 = parse_state_set_literal(node.left.value)  # phi states
    states2 = parse_state_set_literal(node.right.value)  # psi states

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        return p | (
            pre(cgs, coalition, p, transition_cache, early_stop=p_indices) & states1
        )

    result = least_fixpoint(states2, update_with_skip)
    node.value = state_set_to_str(result)
