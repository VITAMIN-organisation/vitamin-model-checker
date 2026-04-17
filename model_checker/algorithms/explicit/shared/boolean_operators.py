"""
Shared boolean operator handlers for set-based model checkers.

Used by ATL, CTL, RBATL, RABATL, OATL, OL. Node values are deterministic string
reprs of state sets (parse_state_set_literal accepts set or str). These helpers
parse, apply the set operation, and store the result via state_set_to_str.
"""

from typing import Any

from model_checker.algorithms.explicit.shared import (
    normalize_state_set,
    state_set_to_str,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs import CGSProtocol


def handle_not(cgs: CGSProtocol, node: Any, normalize_result: bool = False) -> None:
    """Set node to the complement of the left child's state set."""
    states = parse_state_set_literal(node.left.value)
    result = cgs.all_states_set - states
    node.value = state_set_to_str(
        normalize_state_set(result) if normalize_result else result
    )


def handle_or(cgs: CGSProtocol, node: Any, normalize_result: bool = False) -> None:
    """Set node to the union of left and right child state sets."""
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    result = states1 | states2
    node.value = state_set_to_str(
        normalize_state_set(result) if normalize_result else result
    )


def handle_and(cgs: CGSProtocol, node: Any, normalize_result: bool = False) -> None:
    """Set node to the intersection of left and right child state sets."""
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    result = states1 & states2
    node.value = state_set_to_str(
        normalize_state_set(result) if normalize_result else result
    )


def handle_implies(cgs: CGSProtocol, node: Any, normalize_result: bool = False) -> None:
    """Set node to (all_states - left) | right (phi -> psi = not phi or psi)."""
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    result = (cgs.all_states_set - states1) | states2
    node.value = state_set_to_str(
        normalize_state_set(result) if normalize_result else result
    )
