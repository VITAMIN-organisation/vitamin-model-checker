"""Boolean operators on formula tree nodes (AND, OR, NOT, IMPLIES)."""

from typing import Any, Callable, Set

from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs import CGSProtocol


def _serialize_state_set(state_set) -> str:
    return str(tuple(sorted({str(s) for s in state_set})))


def _set_node_state_set(node: Any, state_set) -> None:
    node.value = _serialize_state_set(state_set)


def _binary_state_set(
    node: Any, combine: Callable[[Set[str], Set[str]], Set[str]]
) -> None:
    left = parse_state_set_literal(node.left.value)
    right = parse_state_set_literal(node.right.value)
    _set_node_state_set(node, combine(left, right))


def handle_not(cgs: CGSProtocol, node: Any) -> None:
    """Set node to the complement of the left child's state set."""
    states = parse_state_set_literal(node.left.value)
    _set_node_state_set(node, cgs.all_states_set - states)


def handle_or(_cgs: CGSProtocol, node: Any) -> None:
    """Set node to the union of left and right child state sets."""
    _binary_state_set(node, lambda left, right: left | right)


def handle_and(_cgs: CGSProtocol, node: Any) -> None:
    """Set node to the intersection of left and right child state sets."""
    _binary_state_set(node, lambda left, right: left & right)


def handle_implies(cgs: CGSProtocol, node: Any) -> None:
    """Set node to (all_states - left) | right (phi -> psi = not phi or psi)."""
    left = parse_state_set_literal(node.left.value)
    right = parse_state_set_literal(node.right.value)
    _set_node_state_set(node, (cgs.all_states_set - left) | right)
