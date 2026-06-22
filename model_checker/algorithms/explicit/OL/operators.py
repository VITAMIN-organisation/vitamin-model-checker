"""
OL operator handlers for formula tree evaluation.

Unary: NOT, <Jn>X, <Jn>F, <Jn>G. Binary: OR, AND, IMPLIES, <Jn>U, <Jn>R, <Jn>W.
"""

import re
from typing import Callable, Set

from model_checker.algorithms.explicit.OL.preimage import (
    states_globally_in,
    states_release,
    states_until,
    states_weak,
    states_with_next_in,
    states_within_cost,
)
from model_checker.parsers.syntax_patterns import OL_DEMONIC_BOUND_PREFIX_RE
from model_checker.utils.literals import parse_state_set_literal

_OL_BOUND_RE = OL_DEMONIC_BOUND_PREFIX_RE


def extract_bound(formula_node_value: str) -> int:
    """Extract cost bound from OL operator token like <J27>F."""
    match = _OL_BOUND_RE.match(formula_node_value)
    if not match:
        return 0
    return int(match.group(1))


def handle_demonic_globally(cgs, node):
    """Handle <Jn>G: phi holds while the adversary cannot leave phi within the bound."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = str(
        tuple(sorted({str(s) for s in states_globally_in(cgs, target, bound)}))
    )


def handle_demonic_next(cgs, node):
    """Handle <Jn>X: every affordable step within the bound stays in phi."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = str(
        tuple(sorted({str(s) for s in states_with_next_in(cgs, target, bound)}))
    )


def handle_demonic_eventually(cgs, node):
    """Handle <Jn>F: phi is reachable within accumulated cost bound."""
    bound = extract_bound(node.value)
    target = parse_state_set_literal(node.left.value)
    node.value = str(
        tuple(sorted({str(s) for s in states_within_cost(cgs, target, bound)}))
    )


def handle_demonic_ternary(
    cgs,
    node,
    evaluate: Callable[..., Set[str]],
):
    """Handle <Jn>U, <Jn>R, and <Jn>W from a shared phi/psi/bound evaluation."""
    bound = extract_bound(node.value)
    phi = parse_state_set_literal(node.left.value)
    psi = parse_state_set_literal(node.right.value)
    node.value = str(tuple(sorted({str(s) for s in evaluate(cgs, phi, psi, bound)})))


TERNARY_EVALUATORS = {
    "DEMONIC_UNTIL": states_until,
    "DEMONIC_RELEASE": states_release,
    "DEMONIC_WEAK": states_weak,
}
