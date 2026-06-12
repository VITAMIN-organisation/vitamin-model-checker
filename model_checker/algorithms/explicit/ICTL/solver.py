"""Formula tree solver for ICTL."""

from typing import TYPE_CHECKING, Any, Optional

from model_checker.algorithms.explicit.ICTL.operators import (
    handle_af,
    handle_ag,
    handle_and,
    handle_ar,
    handle_au,
    handle_ax,
    handle_ef,
    handle_eg,
    handle_er,
    handle_eu,
    handle_ex,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formulas.ICTL.ictl_ply_parser import verifyICTL

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode


def _unary_handler(
    checker: "ICTLModelChecker", node: "FormulaTreeNode"
) -> Optional[Any]:
    val = node.value
    if verifyICTL("NOT", val):
        return handle_not
    if verifyICTL("FORALL", val) and verifyICTL("NEXT", val):
        return handle_ax
    if verifyICTL("EXIST", val) and verifyICTL("NEXT", val):
        return handle_ex
    if verifyICTL("EXIST", val) and verifyICTL("GLOBALLY", val):
        return handle_eg
    if verifyICTL("FORALL", val) and verifyICTL("GLOBALLY", val):
        return handle_ag
    if verifyICTL("EXIST", val) and verifyICTL("EVENTUALLY", val):
        return handle_ef
    if verifyICTL("FORALL", val) and verifyICTL("EVENTUALLY", val):
        return handle_af
    return None


def _binary_handler(
    checker: "ICTLModelChecker", node: "FormulaTreeNode"
) -> Optional[Any]:
    val = node.value
    if verifyICTL("OR", val):
        return handle_or
    if verifyICTL("AND", val):
        return handle_and
    if verifyICTL("IMPLIES", val):
        return handle_implies
    if verifyICTL("EXIST", val) and verifyICTL("UNTIL", val):
        return handle_eu
    if verifyICTL("FORALL", val) and verifyICTL("UNTIL", val):
        return handle_au
    if verifyICTL("EXIST", val) and verifyICTL("RELEASE", val):
        return handle_er
    if verifyICTL("FORALL", val) and verifyICTL("RELEASE", val):
        return handle_ar
    return None


def solve_tree(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    """Evaluate the formula tree bottom-up."""
    if node.left is not None:
        solve_tree(checker, node.left)
    if node.right is not None:
        solve_tree(checker, node.right)

    if node.right is None:
        handler = _unary_handler(checker, node)
        if handler is not None:
            handler(checker, node)
        return

    if node.left is not None and node.right is not None:
        handler = _binary_handler(checker, node)
        if handler is not None:
            handler(checker, node)
