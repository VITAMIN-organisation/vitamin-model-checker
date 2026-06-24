"""Coalition operator handlers shared by RABATL and RBATL."""

from collections.abc import Callable

from model_checker.algorithms.explicit.shared.bound_utils import (
    extract_coalition_and_bound,
    inc_bound,
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


def _accumulate_over_bound_allocations(
    cgs,
    coalition,
    bound,
    trans_cache,
    cost_filter: CostFilter,
    initial_target,
    mask,
):
    """Enumerate budget vectors and accumulate states reachable under each allocation."""
    accumulated = set()
    curr_bound_p = [0] * len(bound)
    zero_bound = [0] * len(bound)
    while True:
        remaining_bound = [
            max(0, x - y) for x, y in zip(bound, curr_bound_p, strict=True)
        ]
        reachable = (
            compute_pre_states(
                cgs,
                coalition,
                initial_target,
                remaining_bound,
                trans_cache,
                cost_filter,
            )
            & mask
        )
        while reachable - accumulated:
            accumulated.update(reachable)
            reachable = (
                compute_pre_states(
                    cgs,
                    coalition,
                    accumulated,
                    zero_bound,
                    trans_cache,
                    cost_filter,
                )
                & mask
            )
        if not inc_bound(curr_bound_p, bound):
            break
    return accumulated


def _evaluate_bounded_coalition_operator(
    cgs,
    coalition,
    bound,
    trans_cache,
    cost_filter: CostFilter,
    fixpoint: Callable,
    fixpoint_start,
    bounded_initial,
    mask,
):
    """Run a fixpoint when the budget is zero, else enumerate budget allocations."""
    if not any(bound):

        def update(states):
            return (
                compute_pre_states(
                    cgs, coalition, states, bound, trans_cache, cost_filter
                )
                & mask
            )

        return fixpoint(fixpoint_start, update)

    return _accumulate_over_bound_allocations(
        cgs,
        coalition,
        bound,
        trans_cache,
        cost_filter,
        bounded_initial,
        mask,
    )


def handle_coalition_globally(cgs, node, cost_filter: CostFilter) -> None:
    """Handle <J><b>G: coalition keeps phi forever within resource bounds."""
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
        target_states,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_next(cgs, node, cost_filter: CostFilter) -> None:
    """Handle <J><b>X: coalition forces a next state within resource bounds."""
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
    """Handle <J><b>F: coalition eventually reaches phi within resource bounds."""
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
        target_states,
        cgs.all_states_set,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_until(cgs, node, cost_filter: CostFilter) -> None:
    """Handle <J><b>U: coalition reaches psi while maintaining phi within bounds."""
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
        psi_states,
        phi_states,
    )
    node.value = str(tuple(sorted({str(s) for s in result})))
