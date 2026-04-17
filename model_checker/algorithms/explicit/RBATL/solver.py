"""
Formula tree solver for RBATL model checking.

This module contains the solve_tree function that recursively evaluates
RBATL formula trees using bottom-up evaluation.
"""

from model_checker.algorithms.explicit.RBATL.operators import (
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


def _get_parser():
    return FormulaParserFactory.get_parser_instance("RBATL")


_UNARY = {
    "NOT": handle_not,
    "COALITION_GLOBALLY": handle_coalition_globally,
    "COALITION_NEXT": handle_coalition_next,
    "COALITION_EVENTUALLY": handle_coalition_eventually,
}
_BINARY = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
    "COALITION_UNTIL": handle_coalition_until,
}


def _rbatl_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("COALITION_BOUND", val):
        if parser_instance.verify("GLOBALLY", val):
            return "COALITION_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "COALITION_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "COALITION_EVENTUALLY"
    return None


def _rbatl_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("COALITION_BOUND", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return "COALITION_UNTIL"
    return None


def solve_tree(cgs, node, cache=None):
    """
    Recursively solve the RBATL formula tree.
    """
    if cache is None:
        cache = {}

    node_key = (
        str(node.value)
        + (str(node.left) if node.left else "")
        + (str(node.right) if node.right else "")
    )
    if node_key in cache:
        node.value = cache[node_key]
        return

    if node.left:
        solve_tree(cgs, node.left, cache)
    if node.right:
        solve_tree(cgs, node.right, cache)

    val = node.value
    if node.right is None:
        key = _rbatl_unary_key(_get_parser(), val)
        if key and key in _UNARY:
            _UNARY[key](cgs, node)
    elif node.left and node.right:
        key = _rbatl_binary_key(_get_parser(), val)
        if key and key in _BINARY:
            _BINARY[key](cgs, node)

    cache[node_key] = node.value
