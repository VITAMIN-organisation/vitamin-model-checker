"""Wallet_ATL operator handlers for formula tree evaluation, following AAMAS26b
Algorithm 1: every operator is built on wPre(Pre(A, S)), the coalition pre-image
kept only where the wallet guards hold."""

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


def _guarded_pre(cgs, node, transition_cache):
    """The step S -> wPre(Pre(A, S)) for the node's `<<A:C>>` prefix. The guard
    depends only on the state, so its states are computed once."""
    coalition, constraints = extract_coalition_and_constraints(node.value)
    guard_states = apply_wallet_constraints(cgs, constraints, cgs.all_states_set)

    def step(states, early_stop=None):
        return (
            pre(cgs, coalition, states, transition_cache, early_stop=early_stop)
            & guard_states
        )

    return step


def _until(cgs, step, keep, goal):
    """Least fixpoint of rho | (wPre(Pre(A, rho)) & keep) from `goal`, with no
    wallet filter on `goal` (Algorithm 1 lines 18-25, line 20)."""

    def update(p):
        # early_stop only saves work: states already in p are kept by `p |`.
        return p | (step(p, early_stop=state_names_to_indices(cgs, p)) & keep)

    return least_fixpoint(goal, update)


def _store(node, states):
    node.value = str(tuple(sorted({str(s) for s in states})))


def handle_wallet_coalition_globally(cgs, node, transition_cache):
    """Greatest fixpoint of wPre(Pre(A, rho)) & [[phi]] (Algorithm 1 lines 10-17)."""
    step = _guarded_pre(cgs, node, transition_cache)
    phi = parse_state_set_literal(node.left.value)
    _store(node, greatest_fixpoint(cgs.all_states_set.copy(), lambda p: step(p) & phi))


def handle_wallet_coalition_next(cgs, node, transition_cache):
    """wPre(Pre(A, [[phi]])) (Algorithm 1 line 9): the next state need not
    satisfy the guard."""
    step = _guarded_pre(cgs, node, transition_cache)
    _store(node, step(parse_state_set_literal(node.left.value)))


def handle_wallet_coalition_eventually(cgs, node, transition_cache):
    """`<<A:C>>F phi` as `<<A:C>>true U phi`; F is not in the paper's grammar."""
    step = _guarded_pre(cgs, node, transition_cache)
    goal = parse_state_set_literal(node.left.value)
    _store(node, _until(cgs, step, cgs.all_states_set, goal))


def handle_wallet_coalition_until(cgs, node, transition_cache):
    """`<<A:C>>phi U psi` (Algorithm 1 lines 18-25)."""
    step = _guarded_pre(cgs, node, transition_cache)
    phi = parse_state_set_literal(node.left.value)
    psi = parse_state_set_literal(node.right.value)
    _store(node, _until(cgs, step, phi, psi))
