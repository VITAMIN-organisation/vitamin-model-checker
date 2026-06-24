"""Formula tree solver for Wallet_ATL model checking."""

from typing import Any

from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

from .operators import (
    handle_wallet_coalition_eventually,
    handle_wallet_coalition_globally,
    handle_wallet_coalition_next,
    handle_wallet_coalition_until,
)
from .preimage import is_wallet_coalition_operator

_UNARY = {
    "NOT": lambda c, n, tc: handle_not(c, n),
    "COALITION_GLOBALLY": handle_wallet_coalition_globally,
    "COALITION_NEXT": handle_wallet_coalition_next,
    "COALITION_EVENTUALLY": handle_wallet_coalition_eventually,
}
_BINARY = {
    "OR": lambda c, n, tc: handle_or(c, n),
    "COALITION_UNTIL": handle_wallet_coalition_until,
    "AND": lambda c, n, tc: handle_and(c, n),
    "IMPLIES": lambda c, n, tc: handle_implies(c, n),
}


def _walletatl_unary_key(parser_instance: Any, val: Any) -> str | None:
    if parser_instance.verify("NOT", val):
        return "NOT"
    if is_wallet_coalition_operator(val):
        if parser_instance.verify("GLOBALLY", val):
            return "COALITION_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "COALITION_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "COALITION_EVENTUALLY"
    return None


def _walletatl_binary_key(parser_instance: Any, val: Any) -> str | None:
    if parser_instance.verify("OR", val):
        return "OR"
    if is_wallet_coalition_operator(val) and parser_instance.verify("UNTIL", val):
        return "COALITION_UNTIL"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    return None


def solve_tree(cgs, node, transition_cache: dict | None = None) -> None:
    """Recursively solve Wallet_ATL formula tree bottom-up."""
    if node.left is not None:
        solve_tree(cgs, node.left, transition_cache)
    if node.right is not None:
        solve_tree(cgs, node.right, transition_cache)

    parser_instance = FormulaParserFactory.get_parser_instance("Wallet_ATL")
    if node.right is None:
        key = _walletatl_unary_key(parser_instance, node.value)
        if key and key in _UNARY:
            _UNARY[key](cgs, node, transition_cache)
    elif node.left is not None and node.right is not None:
        key = _walletatl_binary_key(parser_instance, node.value)
        if key and key in _BINARY:
            _BINARY[key](cgs, node, transition_cache)
