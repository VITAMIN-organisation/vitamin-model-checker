"""Formula tree solver for ICTL - migrated to use shared solver_core."""

from typing import TYPE_CHECKING, Any

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
from model_checker.algorithms.explicit.shared.solver_core import solve_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode


# Operator mappings for solver_core
_UNARY_OPERATORS = {
    "NOT": handle_not,
    "AX": handle_ax,
    "EX": handle_ex,
    "AG": handle_ag,
    "EG": handle_eg,
    "AF": handle_af,
    "EF": handle_ef,
}

_BINARY_OPERATORS = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
    "AU": handle_au,
    "EU": handle_eu,
    "AR": handle_ar,
    "ER": handle_er,
}


def _ictl_unary_key(parser_instance: Any, val: Any) -> str | None:
    """Map node value to unary operator key."""
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("NEXT", val):
        return "AX"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("NEXT", val):
        return "EX"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return "AG"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("GLOBALLY", val):
        return "EG"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "AF"
    if parser_instance.verify("EXIST", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "EF"
    return None


def _ictl_binary_key(parser_instance: Any, val: Any) -> str | None:
    """Map node value to binary operator key."""
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("UNTIL", val):
        return "EU"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("UNTIL", val):
        return "AU"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("RELEASE", val):
        return "ER"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("RELEASE", val):
        return "AR"
    return None


# Boolean operators that don't need extra processing
_BOOLEAN_KEYS = {"OR", "AND", "IMPLIES", "NOT"}


def solve_tree(
    checker: "ICTLModelChecker",
    node: "FormulaTreeNode",
    parser: Any | None = None,
) -> None:
    """Evaluate the ICTL formula tree bottom-up using shared solver_core."""
    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("ICTL")

    solve_formula_tree(
        checker,  # Pass checker as the first argument
        node,
        parser,
        _UNARY_OPERATORS,
        _BINARY_OPERATORS,
        _ictl_unary_key,
        _ictl_binary_key,
        _BOOLEAN_KEYS,
        extra_args=(),
    )
