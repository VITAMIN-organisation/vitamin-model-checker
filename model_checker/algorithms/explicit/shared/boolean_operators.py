"""Boolean operators on formula tree nodes (AND, OR, NOT, IMPLIES)."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.shared.boolean_semantics import (
    compute_boolean_result,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    pass


def _set_node_state_set(node: Any, state_set) -> None:
    node.value = str(tuple(sorted({str(s) for s in state_set})))


def _binary_state_set(
    node: Any, combine: Callable[[set[str], set[str]], set[str]]
) -> None:
    left = parse_state_set_literal(node.left.value)
    right = parse_state_set_literal(node.right.value)
    _set_node_state_set(node, combine(left, right))


def handle_not(cgs: CGSProtocol, node: Any) -> None:
    """Set node to the complement of the left child's state set."""
    left = parse_state_set_literal(node.left.value)
    result = compute_boolean_result("NOT", left, all_states=cgs.all_states_set)
    _set_node_state_set(node, result)


def handle_or(_cgs: CGSProtocol, node: Any) -> None:
    """Set node to the union of left and right child state sets."""
    _binary_state_set(
        node, lambda left, right: compute_boolean_result("OR", left, right_states=right)
    )


def handle_and(_cgs: CGSProtocol, node: Any) -> None:
    """Set node to the intersection of left and right child state sets."""
    _binary_state_set(
        node,
        lambda left, right: compute_boolean_result("AND", left, right_states=right),
    )


def handle_implies(cgs: CGSProtocol, node: Any) -> None:
    """Set node to (all_states - left) | right (phi -> psi = not phi or psi)."""
    left = parse_state_set_literal(node.left.value)
    right = parse_state_set_literal(node.right.value)
    result = compute_boolean_result(
        "IMPLIES", left, right_states=right, all_states=cgs.all_states_set
    )
    _set_node_state_set(node, result)
