"""Formula tree solver for CTL model checking."""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.CTL.operators import (
    handle_af,
    handle_ag,
    handle_ar,
    handle_au,
    handle_ax,
    handle_ef,
    handle_eg,
    handle_er,
    handle_eu,
    handle_ex,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.algorithms.explicit.shared.solver_core import solve_formula_tree

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


_UNARY = {
    "NOT": handle_not,
    "EX": handle_ex,
    "AX": handle_ax,
    "EF": handle_ef,
    "AF": handle_af,
    "EG": handle_eg,
    "AG": handle_ag,
    "AR": handle_ar,
}
_BINARY = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
    "EU": handle_eu,
    "AU": handle_au,
    "ER": handle_er,
}


def _ctl_unary_key(parser_instance: Any, val: Any) -> str | None:
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("NEXT", val):
        return "EX"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("NEXT", val):
        return "AX"
    if parser_instance.verify("EXIST", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "EF"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "AF"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("GLOBALLY", val):
        return "EG"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return "AG"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("RELEASE", val):
        return "AR"
    return None


def _ctl_binary_key(parser_instance: Any, val: Any) -> str | None:
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
    return None


def operator_key(parser: Any, node: Any) -> str | None:
    """The operator of an unsolved node (EX, AU, AND, ...), or None for an atom."""
    if node.right is None:
        return _ctl_unary_key(parser, node.value)
    if node.left is not None:
        return _ctl_binary_key(parser, node.value)
    return None


def solve_tree(cgs: "CGS", root: Any, parser: Any) -> None:
    """Evaluate the formula tree bottom-up; each node's value becomes its state set."""
    solve_formula_tree(
        cgs, root, parser, _UNARY, _BINARY, _ctl_unary_key, _ctl_binary_key, set()
    )
