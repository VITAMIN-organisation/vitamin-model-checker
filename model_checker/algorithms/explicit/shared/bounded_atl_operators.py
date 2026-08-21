"""Coalition operator handlers shared by RABATL and RBATL."""

from collections.abc import Callable

from model_checker.algorithms.explicit.shared.bound_utils import (
    extract_coalition_and_bound,
)
from model_checker.algorithms.explicit.shared.bounded_atl_preimage import (
    CostFilter,
    build_transition_cache,
    compute_pre_states,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.utils.literals import parse_state_set_literal


def _evaluate_bounded_coalition_operator(
    cgs,
    coalition,
    bound,
    trans_cache,
    cost_filter: CostFilter,
    fixpoint: Callable,
    fixpoint_start,
    mask,
):
    """Evaluate a temporal coalition operator under a per-step resource budget.

    Every forced transition must stay within ``bound``; the budget is not spent
    across the path. ``mask`` restricts intermediate states (for example phi in U).
    """

    def update(states):
        return states | (
            compute_pre_states(cgs, coalition, states, bound, trans_cache, cost_filter)
            & mask
        )

    if fixpoint is greatest_fixpoint:

        def gfp_update(states):
            return (
                compute_pre_states(
                    cgs, coalition, states, bound, trans_cache, cost_filter
                )
                & mask
            )

        return greatest_fixpoint(fixpoint_start, gfp_update)

    return least_fixpoint(fixpoint_start, update)


def handle_coalition_globally(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can keep phi forever within the resource bound."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result = _evaluate_bounded_coalition_operator(
        cgs,
        coalition,
        bound,
        trans_cache,
        cost_filter,
        greatest_fixpoint,
        cgs.all_states_set.copy(),
        target_states,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_next(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force phi in one affordable step."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result = compute_pre_states(
        cgs,
        coalition,
        target_states,
        bound,
        trans_cache,
        cost_filter,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_eventually(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force phi eventually within the resource bound."""
    coalition, bound = extract_coalition_and_bound(node.value)
    target_states = parse_state_set_literal(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result = _evaluate_bounded_coalition_operator(
        cgs,
        coalition,
        bound,
        trans_cache,
        cost_filter,
        least_fixpoint,
        target_states,
        cgs.all_states_set,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_until(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force psi while keeping phi within the bound."""
    coalition, bound = extract_coalition_and_bound(node.value)
    phi_states = parse_state_set_literal(node.left.value)
    psi_states = parse_state_set_literal(node.right.value)
    trans_cache = build_transition_cache(cgs, coalition)
    result = _evaluate_bounded_coalition_operator(
        cgs,
        coalition,
        bound,
        trans_cache,
        cost_filter,
        least_fixpoint,
        psi_states,
        phi_states,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))
