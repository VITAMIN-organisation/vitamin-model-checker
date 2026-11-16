"""Coalition operator handlers shared by RABATL and RBATL."""

import itertools
import math
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
from model_checker.utils.literals import parse_state_set_literal, state_set_literal

# solve_budget(free_pre, paid) returns the states won with one budget, where
# free_pre(X) is the cost-0 pre-image of X and paid the states won by one paid move.
BudgetSolver = Callable[[Callable[[set[str]], set[str]], set[str]], set[str]]

# Measured: 90601 budgets, bound (300,300), take 5.9 s on the 8-state sensor model.
MAX_BUDGETS = 100_000


def _solve_with_cumulative_bound(
    cgs, coalition, bound, cost_filter: CostFilter, solve_budget: BudgetSolver
) -> set[str]:
    """The states won with total cost at most ``bound``, solving every smaller budget
    first: a move that costs c leaves the budget minus c for the rest of the path."""
    budget_count = math.prod(b + 1 for b in bound)
    if budget_count > MAX_BUDGETS:
        raise ValueError(
            f"[VALIDATION] Bound {bound} needs {budget_count} budgets (the product of "
            f"b_i + 1); the checker solves at most {MAX_BUDGETS}."
        )
    trans_cache = build_transition_cache(cgs, coalition, cost_filter)
    zero = [0] * len(bound)
    # The cost-0 pre-image does not depend on the budget, and fixpoints of
    # different budgets meet the same sets.
    free_cache: dict[frozenset[str], set[str]] = {}

    def free_pre(states):
        key = frozenset(states)
        if key not in free_cache:
            free_cache[key] = compute_pre_states(cgs, states, zero, trans_cache)
        return free_cache[key]

    # Each won set with the smallest budgets that reach it: a larger budget with the
    # same set leaves less for the paid move, so its pre-image adds nothing.
    cheapest: dict[frozenset[str], list[tuple[int, ...]]] = {}
    states: set[str]
    # Lexicographic order lists every componentwise smaller budget first.
    for budget in itertools.product(*(range(b + 1) for b in bound)):
        paid: set[str] = set()
        for won, budgets in cheapest.items():
            if not won:
                continue
            for smaller in budgets:
                if _fits(smaller, budget):
                    left = [b - s for s, b in zip(smaller, budget, strict=True)]
                    paid |= compute_pre_states(cgs, set(won), left, trans_cache)
        states = solve_budget(free_pre, paid)
        budgets = cheapest.setdefault(frozenset(states), [])
        if not any(_fits(smaller, budget) for smaller in budgets):
            budgets.append(budget)
    return states


def _fits(smaller: tuple[int, ...], budget: tuple[int, ...]) -> bool:
    return all(s <= b for s, b in zip(smaller, budget, strict=True))


def _until_states(cgs, coalition, bound, cost_filter, phi_states, psi_states):
    """States where the coalition forces psi, keeping phi until then, within bound."""

    def solve_budget(free_pre, paid):
        return least_fixpoint(
            psi_states,
            lambda states: states | ((free_pre(states) | paid) & phi_states),
        )

    return _solve_with_cumulative_bound(
        cgs, coalition, bound, cost_filter, solve_budget
    )


def handle_coalition_globally(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can keep phi forever within the resource bound."""
    coalition, bound = extract_coalition_and_bound(node.value, cgs)
    target_states = parse_state_set_literal(node.left.value)

    def solve_budget(free_pre, paid):
        return greatest_fixpoint(
            cgs.all_states_set,
            lambda states: (free_pre(states) | paid) & target_states,
        )

    result = _solve_with_cumulative_bound(
        cgs, coalition, bound, cost_filter, solve_budget
    )
    node.value = state_set_literal(result)


def handle_coalition_next(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force phi in one affordable step."""
    coalition, bound = extract_coalition_and_bound(node.value, cgs)
    target_states = parse_state_set_literal(node.left.value)
    trans_cache = build_transition_cache(cgs, coalition, cost_filter)
    result = compute_pre_states(cgs, target_states, bound, trans_cache)
    node.value = state_set_literal(result)


def handle_coalition_eventually(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force phi eventually within the resource bound."""
    coalition, bound = extract_coalition_and_bound(node.value, cgs)
    target_states = parse_state_set_literal(node.left.value)
    result = _until_states(
        cgs, coalition, bound, cost_filter, cgs.all_states_set, target_states
    )
    node.value = state_set_literal(result)


def handle_coalition_until(cgs, node, cost_filter: CostFilter) -> None:
    """States where the coalition can force psi while keeping phi within the bound."""
    coalition, bound = extract_coalition_and_bound(node.value, cgs)
    phi_states = parse_state_set_literal(node.left.value)
    psi_states = parse_state_set_literal(node.right.value)
    result = _until_states(cgs, coalition, bound, cost_filter, phi_states, psi_states)
    node.value = state_set_literal(result)
