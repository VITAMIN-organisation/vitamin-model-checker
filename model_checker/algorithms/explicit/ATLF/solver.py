"""
Formula tree solver for ATLF model checking.

This module contains the solve_tree function that recursively evaluates
ATLF formula trees using bottom-up evaluation with real-valued semantics.
"""

from model_checker.algorithms.explicit.ATLF.operators import (
    handle_and,
    handle_coalition_eventually,
    handle_coalition_globally,
    handle_coalition_next,
    handle_coalition_until,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _get_parser():
    return FormulaParserFactory.get_parser_instance("ATL")


def solve_tree(cgs, node):
    """
    Recursively solve the formula tree for ATLF.

    The result is the model checking result with real-valued state lists.
    It solves every node depending on the operator.
    """
    if node.left is not None:
        solve_tree(cgs, node.left)
    if node.right is not None:
        solve_tree(cgs, node.right)

    # Handle unary operators
    if node.right is None:
        if _get_parser().verify("NOT", node.value):
            handle_not(cgs, node)
        elif _get_parser().verify("COALITION", node.value) and _get_parser().verify(
            "GLOBALLY", node.value
        ):
            handle_coalition_globally(cgs, node)
        elif _get_parser().verify("COALITION", node.value) and _get_parser().verify(
            "NEXT", node.value
        ):
            handle_coalition_next(cgs, node)
        elif _get_parser().verify("COALITION", node.value) and _get_parser().verify(
            "EVENTUALLY", node.value
        ):
            handle_coalition_eventually(cgs, node)

    # Handle binary operators
    if node.left is not None and node.right is not None:
        if _get_parser().verify("OR", node.value):
            handle_or(cgs, node)
        elif _get_parser().verify("AND", node.value):
            handle_and(cgs, node)
        elif _get_parser().verify("COALITION", node.value) and _get_parser().verify(
            "UNTIL", node.value
        ):
            handle_coalition_until(cgs, node)
        elif _get_parser().verify("IMPLIES", node.value):
            handle_implies(cgs, node)
