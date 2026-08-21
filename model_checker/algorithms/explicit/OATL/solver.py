"""Bottom-up formula tree solver for OATL model checking."""

from model_checker.algorithms.explicit.OATL.operators import (
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
from model_checker.algorithms.explicit.shared.solver_core import solve_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

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


def _oatl_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("COALITION_DEMONIC", val):
        if parser_instance.verify("GLOBALLY", val):
            return "COALITION_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "COALITION_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "COALITION_EVENTUALLY"
    return None


def _oatl_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("COALITION_DEMONIC", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return "COALITION_UNTIL"
    return None


def solve_tree(cgs, node, solve_context, cache=None):
    """
    Recursively solve the formula tree for OATL.
    """
    if cache is None:
        cache = {}


def solve_tree(cgs, node, solve_context):
    """Recursively solve the OATL formula tree."""
    parser = FormulaParserFactory.get_parser_instance("OATL")
    solve_formula_tree(
        cgs,
        node,
        parser,
        _UNARY,
        _BINARY,
        _oatl_unary_key,
        _oatl_binary_key,
        {"NOT", "AND", "OR", "IMPLIES"},
        extra_args=(solve_context,),
    )
