"""COTL coalition temporal operator handlers (index-space fixpoints)."""

from model_checker.algorithms.explicit.shared.cost_utils import (
    extract_coalition_and_cost,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.utils.literals import parse_state_set_literal

from .preimage import cross_index


def _format_index_result(cgs, state_indices):
    names = {str(s) for s in state_indices_to_names(cgs, state_indices)}
    return str(tuple(sorted(names)))


def _coalition_cross(cgs, node, solve_context):
    """Bind coalition, cost bound, and a cost-bounded pre-image step for this node."""
    coalition, cost_bound = extract_coalition_and_cost(node.value)
    agents_set = solve_context["agents_set_for"](coalition)
    base_action_cache = cgs._base_action_cache

    def cross(state_indices):
        return cross_index(
            cgs,
            cost_bound,
            coalition,
            state_indices,
            solve_context,
            agents_set,
            base_action_cache,
        )

    return cross


def handle_coalition_globally(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    phi_indices = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))

    def update(states):
        return phi_indices & cross(states)

    node.value = _format_index_result(cgs, greatest_fixpoint(phi_indices, update))


def handle_coalition_next(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    target_indices = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    node.value = _format_index_result(cgs, cross(target_indices))


def handle_coalition_eventually(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    phi_indices = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))
    all_states_index = solve_context["all_states_index"]

    def update(states):
        return phi_indices | (all_states_index & cross(states))

    node.value = _format_index_result(cgs, least_fixpoint(phi_indices, update))


def handle_coalition_until(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    left_indices = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))
    right_indices = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )

    def update(states):
        return right_indices | (left_indices & cross(states))

    node.value = _format_index_result(cgs, least_fixpoint(right_indices, update))


def handle_coalition_release(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    left_indices = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))
    right_indices = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )

    def update(states):
        return right_indices & (left_indices | cross(states))

    node.value = _format_index_result(cgs, greatest_fixpoint(right_indices, update))


def handle_coalition_weak(cgs, node, solve_context):
    cross = _coalition_cross(cgs, node, solve_context)
    release_indices = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )
    weak_indices = state_names_to_indices(
        cgs,
        parse_state_set_literal(node.left.value)
        | parse_state_set_literal(node.right.value),
    )

    def update(states):
        return weak_indices & (release_indices | cross(states))

    node.value = _format_index_result(cgs, greatest_fixpoint(weak_indices, update))
