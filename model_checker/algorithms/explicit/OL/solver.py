"""
Formula tree solver for OL model checking.

Recursively evaluates OL formula trees using bottom-up evaluation.
"""

from model_checker.algorithms.explicit.OL.operators import (
    TERNARY_EVALUATORS,
    handle_demonic_eventually,
    handle_demonic_globally,
    handle_demonic_next,
    handle_demonic_ternary,
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
    "DEMONIC_GLOBALLY": handle_demonic_globally,
    "DEMONIC_NEXT": handle_demonic_next,
    "DEMONIC_EVENTUALLY": handle_demonic_eventually,
}
_BINARY = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
}


def _ol_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("DEMONIC", val):
        if parser_instance.verify("GLOBALLY", val):
            return "DEMONIC_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "DEMONIC_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "DEMONIC_EVENTUALLY"
    return None


def _ol_ternary_key(parser_instance, val):
    if not parser_instance.verify("DEMONIC", val):
        return None
    if parser_instance.verify("UNTIL", val):
        return "DEMONIC_UNTIL"
    if parser_instance.verify("RELEASE", val):
        return "DEMONIC_RELEASE"
    if parser_instance.verify("WEAK", val):
        return "DEMONIC_WEAK"
    return None


def _ol_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    return None


def solve_tree(cgs, node, cache: dict = None):
    """Recursively solve the OL formula tree."""
    if cache is None:
        cache = {}

    parser = FormulaParserFactory.get_parser_instance("OL")
    solve_formula_tree(
        cgs,
        node,
        parser,
        _UNARY,
        _BINARY,
        _ol_unary_key,
        _ol_binary_key,
        {"NOT", "AND", "OR", "IMPLIES"},
        extra_args=(),
        ternary_map=TERNARY_EVALUATORS,
        ternary_key_fn=_ol_ternary_key,
        ternary_handler=handle_demonic_ternary,
        cache=cache,
    )
