"""Formula tree solver for IATL."""

from typing import TYPE_CHECKING, Any, Optional

from model_checker.algorithms.explicit.IATL.operators import (
    handle_and,
    handle_coalition_eventually_exists,
    handle_coalition_eventually_forall,
    handle_coalition_globally_exists,
    handle_coalition_globally_forall,
    handle_coalition_next_exists,
    handle_coalition_next_forall,
    handle_coalition_release_exists,
    handle_coalition_release_forall,
    handle_coalition_until_exists,
    handle_coalition_until_forall,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode


def _unary_handler(
    parser_instance: Any, checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> Optional[Any]:
    val = node.value
    if parser_instance.verify("NOT", val):
        return handle_not
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return handle_coalition_globally_exists
    if parser_instance.verify("COALITION_UNIVERSAL", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return handle_coalition_globally_forall
    if parser_instance.verify("COALITION", val) and parser_instance.verify("NEXT", val):
        return handle_coalition_next_exists
    if parser_instance.verify("COALITION_UNIVERSAL", val) and parser_instance.verify(
        "NEXT", val
    ):
        return handle_coalition_next_forall
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return handle_coalition_eventually_exists
    if parser_instance.verify("COALITION_UNIVERSAL", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return handle_coalition_eventually_forall
    return None


def _binary_handler(parser_instance: Any, node: "FormulaTreeNode") -> Optional[Any]:
    val = node.value
    if parser_instance.verify("OR", val):
        return handle_or
    if parser_instance.verify("AND", val):
        return handle_and
    if parser_instance.verify("IMPLIES", val):
        return handle_implies
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return handle_coalition_until_exists
    if parser_instance.verify("COALITION_UNIVERSAL", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return handle_coalition_until_forall
    if parser_instance.verify("COALITION", val) and parser_instance.verify(
        "RELEASE", val
    ):
        return handle_coalition_release_exists
    if parser_instance.verify("COALITION_UNIVERSAL", val) and parser_instance.verify(
        "RELEASE", val
    ):
        return handle_coalition_release_forall
    return None


def solve_tree(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    """Evaluate the formula tree bottom-up."""
    if node.left is not None:
        solve_tree(checker, node.left)
    if node.right is not None:
        solve_tree(checker, node.right)

    parser_instance = FormulaParserFactory.get_parser_instance("IATL")

    if node.right is None:
        handler = _unary_handler(parser_instance, checker, node)
        if handler is not None:
            handler(checker, node)
        return

    if node.left is not None and node.right is not None:
        handler = _binary_handler(parser_instance, node)
        if handler is not None:
            handler(checker, node)
