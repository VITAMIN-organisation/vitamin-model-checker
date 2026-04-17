"""
Formula tree solver for ATL model checking.

This module contains the solve_tree function that recursively evaluates
ATL formula trees using bottom-up evaluation.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from model_checker.algorithms.explicit.ATL.operators import (
    handle_coalition_eventually,
    handle_coalition_globally,
    handle_coalition_next,
    handle_coalition_until,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS

_UNARY = {
    "NOT": lambda c, n, tc: handle_not(c, n),
    "COALITION_GLOBALLY": handle_coalition_globally,
    "COALITION_NEXT": handle_coalition_next,
    "COALITION_EVENTUALLY": handle_coalition_eventually,
}
_BINARY = {
    "OR": lambda c, n, tc: handle_or(c, n),
    "COALITION_UNTIL": handle_coalition_until,
    "AND": lambda c, n, tc: handle_and(c, n),
    "IMPLIES": lambda c, n, tc: handle_implies(c, n),
}


def _get_atl_parser() -> Any:
    """Return the shared ATL parser instance."""
    return FormulaParserFactory.get_parser_instance("ATL")


def _atl_unary_key(parser_instance: Any, val: Any) -> Optional[str]:
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return "COALITION_GLOBALLY"
    if parser_instance.verify("COALITION", val) and parser_instance.verify("NEXT", val):
        return "COALITION_NEXT"
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "COALITION_EVENTUALLY"
    return None


def _atl_binary_key(parser_instance: Any, val: Any) -> Optional[str]:
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return "COALITION_UNTIL"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    return None


def solve_tree(
    cgs: "CGS", node: Any, transition_cache: Optional[Dict[str, Any]] = None
) -> None:
    """
    Recursively solve the formula tree bottom-up.

    Formula is parsed into a binary tree structure. Leaf nodes are atomic
    propositions (resolved to state sets). Internal nodes apply operators
    to combine child results. Each node's value becomes the set of states
    satisfying that subformula.

    Args:
        cgs: The CGS model instance
        node: Current tree node to evaluate
        transition_cache: Optional pre-computed transitions (for performance)
    """
    if node.left is not None:
        solve_tree(cgs, node.left, transition_cache)
    if node.right is not None:
        solve_tree(cgs, node.right, transition_cache)

    val = node.value
    parser_instance = _get_atl_parser()
    if node.right is None:
        key = _atl_unary_key(parser_instance, val)
        if key and key in _UNARY:
            _UNARY[key](cgs, node, transition_cache)
    elif node.left is not None and node.right is not None:
        key = _atl_binary_key(parser_instance, val)
        if key and key in _BINARY:
            _BINARY[key](cgs, node, transition_cache)
