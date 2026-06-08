"""Wallet_ATL operator handlers for formula tree evaluation."""

from model_checker.algorithms.explicit.shared import state_set_to_str
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.engine.runner import parse_state_set_literal

from .preimage import (
    apply_wallet_constraints,
    extract_coalition_and_constraints,
    pre,
)


def _all_agents_coalition(cgs) -> str:
    return ",".join(str(agent) for agent in range(1, cgs.get_number_of_agents() + 1))


# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_globally(cgs, node, transition_cache):
    """Handle G operator using all agents as coalition (legacy Wallet_ATL behavior)."""
    coalition = _all_agents_coalition(cgs)
    states = parse_state_set_literal(node.left.value)

    def update(p):
        return pre(cgs, coalition, p, transition_cache) & states

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = state_set_to_str(result)


def handle_next(cgs, node, transition_cache):
    """Handle X operator using all agents as coalition (legacy Wallet_ATL behavior)."""
    coalition = _all_agents_coalition(cgs)
    states = parse_state_set_literal(node.left.value)
    node.value = state_set_to_str(pre(cgs, coalition, states, transition_cache))


def handle_eventually(cgs, node, transition_cache):
    """Handle F operator using all agents as coalition (legacy Wallet_ATL behavior)."""
    coalition = _all_agents_coalition(cgs)
    states = parse_state_set_literal(node.left.value)

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        return p | pre(cgs, coalition, p, transition_cache, early_stop=p_indices)

    result = least_fixpoint(states, update_with_skip)
    node.value = state_set_to_str(result)


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
    node.value = state_set_to_str(result)


def handle_wallet_coalition_next(cgs, node, transition_cache):
    """Handle <<A:wallet(...)>>X operator."""
    coalition, coalition_agents, constraints = extract_coalition_and_constraints(
        node.value
    )
    states = parse_state_set_literal(node.left.value)

    # Keep legacy behavior from old Wallet_ATL implementation.
    wallet_states = apply_wallet_constraints(cgs, coalition_agents, constraints, states)
    pre_states = pre(cgs, coalition, wallet_states, transition_cache)
    node.value = state_set_to_str(pre_states & wallet_states)


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
    node.value = state_set_to_str(result)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_until(cgs, node, transition_cache):
    """Handle U operator using all agents as coalition (legacy Wallet_ATL behavior)."""
    coalition = _all_agents_coalition(cgs)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update_with_skip(p):
        p_indices = state_names_to_indices(cgs, p)
        return p | (
            pre(cgs, coalition, p, transition_cache, early_stop=p_indices) & states1
        )

    result = least_fixpoint(states2, update_with_skip)
    node.value = state_set_to_str(result)


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
    node.value = state_set_to_str(result)
