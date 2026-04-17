"""
ATLF operator handlers for formula tree evaluation.

This module contains handler functions for all ATLF operators, both unary
(NOT, <A>X, <A>F, <A>G) and binary (OR, AND, IMPLIES, <A>U).

ATLF uses real-valued semantics: each state has a value in [0,1].
"""

from model_checker.algorithms.explicit.ATLF.preimage import (
    build_transition_cache,
    pre,
)
from model_checker.algorithms.explicit.ATLF.real_value_utils import (
    difference_values,
    first_included_in_second,
    intersection_values,
    set_value_tuple_list,
    union_values,
    update_values,
)
from model_checker.engine.runner import parse_tuple_list_literal


def _compute_coalition_globally_fixpoint(cgs, coalition: str, phi_states, trans_cache):
    """
    Greatest fixpoint for <A>G phi with real-valued semantics.

    Starts from value 1 everywhere and iterates until the valuation stabilizes
    under the pre-image and intersection with phi.
    """
    current_value = set_value_tuple_list(cgs, 1)
    candidate = phi_states
    while not first_included_in_second(current_value, candidate):
        current_value = candidate
        pre_result = pre(cgs, coalition, current_value, trans_cache)
        candidate = intersection_values(pre_result, phi_states)
    return current_value


def _compute_coalition_eventually_fixpoint(
    cgs, coalition: str, phi_states, trans_cache
):
    """
    Least fixpoint for <A>F phi with real-valued semantics.

    Starts from value 0 everywhere and iteratively accumulates the valuation
    until the pre-image no longer increases the values.
    """
    current_value = set_value_tuple_list(cgs, 0)
    candidate = phi_states
    while not first_included_in_second(candidate, current_value):
        current_value = update_values(current_value, candidate)
        candidate = pre(cgs, coalition, current_value, trans_cache)
    return current_value


def _compute_coalition_until_fixpoint(
    cgs, coalition: str, phi_states, psi_states, trans_cache
):
    """
    Least fixpoint for <A>(phi U psi) with real-valued semantics.

    Starts from value 0 everywhere and iteratively accumulates the valuation
    based on psi and the constrained pre-image through phi.
    """
    current_value = set_value_tuple_list(cgs, 0)
    candidate = psi_states
    while not first_included_in_second(candidate, current_value):
        current_value = update_values(current_value, candidate)
        pre_result = pre(cgs, coalition, current_value, trans_cache)
        candidate = intersection_values(pre_result, phi_states)
    return current_value


def _parse_real_values(value):
    """Parse real-valued state list from string or return as-is if already a list."""
    if isinstance(value, str):
        return parse_tuple_list_literal(value)
    return value


# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_not(cgs, node):
    """Handle NOT operator: not phi := 1 - phi."""
    states = _parse_real_values(node.left.value)
    ris = difference_values(set_value_tuple_list(cgs, 1), states)
    node.value = str(ris)


def handle_coalition_globally(cgs, node):
    """Handle <A>G operator: coalition can ensure phi forever."""
    coalition = node.value[1:-2]
    states = _parse_real_values(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result_states = _compute_coalition_globally_fixpoint(
        cgs, coalition, states, trans_cache
    )
    node.value = str(result_states)


def handle_coalition_next(cgs, node):
    """Handle <A>X operator: coalition can force next state."""
    coalition = node.value[1:-2]
    left_parsed = _parse_real_values(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    ris = pre(cgs, coalition, left_parsed, trans_cache)
    node.value = str(ris)


def handle_coalition_eventually(cgs, node):
    """Handle <A>F operator: coalition can eventually reach phi."""
    coalition = node.value[1:-2]
    states = _parse_real_values(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result_states = _compute_coalition_eventually_fixpoint(
        cgs, coalition, states, trans_cache
    )
    node.value = str(result_states)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_or(cgs, node):
    """Handle OR operator: max of real-valued state lists."""
    states1 = _parse_real_values(node.left.value)
    states2 = _parse_real_values(node.right.value)
    res = union_values(states1, states2)
    node.value = str(res)


def handle_and(cgs, node):
    """Handle AND operator: min of real-valued state lists."""
    states1 = _parse_real_values(node.left.value)
    states2 = _parse_real_values(node.right.value)
    res = intersection_values(states1, states2)
    node.value = str(res)


def handle_implies(cgs, node):
    """Handle IMPLIES operator: phi -> psi = not phi or psi."""
    states1 = _parse_real_values(node.left.value)
    states2 = _parse_real_values(node.right.value)
    not_states1 = difference_values(set_value_tuple_list(cgs, 1), states1)
    ris = union_values(not_states1, states2)
    node.value = str(ris)


def handle_coalition_until(cgs, node):
    """Handle <A>U operator: coalition can ensure psi eventually while maintaining phi."""
    coalition = node.value[1:-2]
    states1 = _parse_real_values(node.left.value)
    states2 = _parse_real_values(node.right.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result_states = _compute_coalition_until_fixpoint(
        cgs, coalition, states1, states2, trans_cache
    )
    node.value = str(result_states)
