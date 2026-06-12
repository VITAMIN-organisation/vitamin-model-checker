"""
OATL operator handlers for formula tree evaluation.

This module contains handler functions for all OATL operators, both unary
(NOT, <Jn>X, <Jn>F, <Jn>G) and binary (OR, AND, IMPLIES, <Jn>U).
"""

from model_checker.algorithms.explicit.OATL.preimage import (
    _base_action_cache,
    has_affordable_action,
    min_action_cost,
)
from model_checker.algorithms.explicit.shared.cost_utils import (
    extract_coalition_and_cost,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    SolveContext,
    cross_state_names,
    dominant_action_indices,
    pre_indices,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.utils.literals import parse_state_set_literal

# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS (NOT in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_globally(cgs, node, solve_context: SolveContext):
    """Handle <Jn>G operator: coalition can ensure phi forever within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    target = parse_state_set_literal(node.left.value)

    def update(p):
        return target & cross_state_names(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            _base_action_cache,
            has_affordable_action,
        )

    result = greatest_fixpoint(cgs.all_states_set.copy(), update)
    node.value = str(tuple(sorted({str(s) for s in result})))


def handle_coalition_next(cgs, node, solve_context: SolveContext):
    """Handle <Jn>X operator: coalition can force next state within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = str(
        tuple(
            sorted(
                {
                    str(s)
                    for s in cross_state_names(
                        cgs,
                        n,
                        coalition,
                        target,
                        solve_context,
                        _base_action_cache,
                        has_affordable_action,
                    )
                }
            )
        )
    )


def handle_coalition_eventually(cgs, node, solve_context: SolveContext):
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
        target_indices = state_names_to_indices(cgs, result)
        potential_pre = {
            str(cgs.get_state_name_by_index(idx))
            for idx in pre_indices(target_indices, solve_context["pre_by_index"])
        }
        candidates = potential_pre - result

        new_states = set()
        for state in candidates:
            state_str = str(state)
            current_min = min_cost_to_reach.get(state_str, float("inf"))
            if current_min != float("inf") and current_min > max_cost:
                continue

            agents = cgs_actions.get_agents_from_coalition(coalition)
            source_idx = cgs.get_index_by_state_name(state_str)
            safe_indices = state_names_to_indices(cgs, result)
            actions = dominant_action_indices(
                cgs,
                source_idx,
                safe_indices,
                agents,
                solve_context["graph"],
                _base_action_cache,
            )
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

    node.value = str(tuple(sorted({str(s) for s in result})))


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS (OR, AND, IMPLIES in shared.boolean_operators)
# ---------------------------------------------------------


def handle_coalition_until(cgs, node, solve_context: SolveContext):
    """Handle <Jn>U operator: coalition can ensure psi eventually while maintaining phi within cost bound."""
    coalition, n = extract_coalition_and_cost(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update_with_skip(p):
        return p | (
            states1
            & cross_state_names(
                cgs,
                n,
                coalition,
                p,
                solve_context,
                _base_action_cache,
                has_affordable_action,
                early_stop=p,
            )
        )

    result = least_fixpoint(states2, update_with_skip)
    node.value = str(tuple(sorted({str(s) for s in result})))
