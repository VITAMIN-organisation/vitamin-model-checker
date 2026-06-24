"""Bottom-up formula tree solver for ATL model checking."""

from typing import TYPE_CHECKING, Any

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


def _atl_unary_key(parser_instance: Any, val: Any) -> str | None:
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


def _atl_binary_key(parser_instance: Any, val: Any) -> str | None:
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
    cgs: "CGS", node: Any, transition_cache: dict[str, Any] | None = None
) -> None:
    """Evaluate the formula tree bottom-up, storing satisfying states at each node."""
    if node.left is not None:
        solve_tree(cgs, node.left, transition_cache)
    if node.right is not None:
        solve_tree(cgs, node.right, transition_cache)

    val = node.value
    parser_instance = FormulaParserFactory.get_parser_instance("ATL")
    if node.right is None:
        key = _atl_unary_key(parser_instance, val)
        if key and key in _UNARY:
            _UNARY[key](cgs, node, transition_cache)
    elif node.left is not None and node.right is not None:
        key = _atl_binary_key(parser_instance, val)
        if key and key in _BINARY:
            _BINARY[key](cgs, node, transition_cache)
