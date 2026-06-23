"""Wallet_ATL operator handlers for formula tree evaluation."""

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.utils.literals import parse_state_set_literal

from .preimage import (
    apply_wallet_constraints,
    extract_coalition_and_constraints,
    pre,
)


def handle_wallet_coalition_globally(cgs, node, transition_cache):
    """Handle <<A:wallet(...)>>G operator."""
    coalition, coalition_agents, constraints = extract_coalition_and_constraints(
        node.value
    )
    states = parse_state_set_literal(node.left.value)
    wallet_states = apply_wallet_constraints(cgs, coalition_agents, constraints, states)

    def update(p):
        pre_states = pre(cgs, coalition, p, transition_cache)
        valid_pre = apply_wallet_constraints(
            cgs, coalition_agents, constraints, pre_states
        )
        return valid_pre & wallet_states

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_wallet_coalition_next(cgs, node, transition_cache):
    """Handle <<A:wallet(...)>>X operator."""
    coalition, coalition_agents, constraints = extract_coalition_and_constraints(
        node.value
    )
    states = parse_state_set_literal(node.left.value)
    wallet_states = apply_wallet_constraints(cgs, coalition_agents, constraints, states)
    pre_states = pre(cgs, coalition, wallet_states, transition_cache)
    node.value = str(tuple(sorted({str(s) for s in pre_states & wallet_states})))


def handle_wallet_coalition_eventually(cgs, node, transition_cache):
    """Handle <<A:wallet(...)>>F operator."""
    coalition, coalition_agents, constraints = extract_coalition_and_constraints(
        node.value
    )
    states = parse_state_set_literal(node.left.value)
    initial_states = apply_wallet_constraints(
        cgs, coalition_agents, constraints, states
    )

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        pre_states = pre(cgs, coalition, p, transition_cache, early_stop=p_indices)
        valid_pre = apply_wallet_constraints(
            cgs, coalition_agents, constraints, pre_states
        )
        return p | valid_pre

    result = least_fixpoint(initial_states, update_with_skip)
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_wallet_coalition_until(cgs, node, transition_cache):
    """Handle <<A:wallet(...)>>U operator."""
    coalition, coalition_agents, constraints = extract_coalition_and_constraints(
        node.value
    )
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        pre_states = pre(cgs, coalition, p, transition_cache, early_stop=p_indices)
        valid_pre = apply_wallet_constraints(
            cgs, coalition_agents, constraints, pre_states
        )
        return p | (valid_pre & states1)

    result = least_fixpoint(states2, update_with_skip)
    node.value = str(tuple(sorted({str(s) for s in result})))
