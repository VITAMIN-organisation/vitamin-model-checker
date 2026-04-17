"""
Formula tree solver for OL model checking.

This module contains the solve_tree function that recursively evaluates
OL formula trees using bottom-up evaluation.
"""

from typing import Dict, List

from model_checker.algorithms.explicit.OL.operators import (
    handle_demonic_eventually,
    handle_demonic_globally,
    handle_demonic_next,
    handle_demonic_until,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _get_parser():
    return FormulaParserFactory.get_parser_instance("OL")


_UNARY = {
    "NOT": lambda c, n, ps: handle_not(c, n),
    "DEMONIC_GLOBALLY": handle_demonic_globally,
    "DEMONIC_NEXT": handle_demonic_next,
    "DEMONIC_EVENTUALLY": handle_demonic_eventually,
}
_BINARY = {
    "OR": lambda c, n, ps: handle_or(c, n),
    "AND": lambda c, n, ps: handle_and(c, n),
    "IMPLIES": lambda c, n, ps: handle_implies(c, n),
    "DEMONIC_UNTIL": handle_demonic_until,
}


def _ol_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("DEMONIC", val):
        if parser_instance.verify("GLOBALLY", val) or parser_instance.verify(
            "RELEASE", val
        ):
            return "DEMONIC_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "DEMONIC_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "DEMONIC_EVENTUALLY"
    return None


def _ol_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("DEMONIC", val) and parser_instance.verify("UNTIL", val):
        return "DEMONIC_UNTIL"
    return None


def solve_tree(cgs, node, pre_sets: List, cache: Dict = None):
    """
    Recursively solve the OL formula tree.
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
        solve_tree(cgs, node.left, pre_sets, cache)
    if node.right:
        solve_tree(cgs, node.right, pre_sets, cache)

    val = node.value
    if node.right is None:
        key = _ol_unary_key(_get_parser(), val)
        if key and key in _UNARY:
            _UNARY[key](cgs, node, pre_sets)
    elif node.left and node.right:
        key = _ol_binary_key(_get_parser(), val)
        if key and key in _BINARY:
            _BINARY[key](cgs, node, pre_sets)

    cache[node_key] = node.value
