"""Bottom-up formula tree solver for COTL."""

from model_checker.algorithms.explicit.COTL.operators import (
    handle_eventually,
    handle_globally,
    handle_next,
    handle_release,
    handle_until,
    handle_weak_next,
    handle_weak_until,
)
from model_checker.algorithms.explicit.COTL.preimage import LegionSteps
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.algorithms.explicit.shared.solver_core import solve_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

_BOOLEAN_KEYS = {"NOT", "AND", "OR", "IMPLIES"}
_UNARY = {
    "NOT": handle_not,
    "NEXT": handle_next,
    "WEAK_NEXT": handle_weak_next,
    "EVENTUALLY": handle_eventually,
    "GLOBALLY": handle_globally,
}
_BINARY = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
    "UNTIL": handle_until,
    "RELEASE": handle_release,
    "WEAK": handle_weak_until,
}


def _operator_key(parser, value, boolean_keys, temporal_keys):
    for key in boolean_keys:
        if parser.verify(key, value):
            return key
    if parser.verify("LEGION", value):
        for key in temporal_keys:
            if parser.verify(key, value):
                return key
    return None


def _unary_key(parser, value):
    return _operator_key(
        parser, value, ("NOT",), ("NEXT", "WEAK_NEXT", "EVENTUALLY", "GLOBALLY")
    )


def _binary_key(parser, value):
    return _operator_key(
        parser, value, ("OR", "AND", "IMPLIES"), ("UNTIL", "RELEASE", "WEAK")
    )


def solve_tree(model, root) -> None:
    """Replace each node value with the set of states satisfying its subformula."""
    solve_formula_tree(
        model,
        root,
        FormulaParserFactory.get_parser_instance("COTL"),
        _UNARY,
        _BINARY,
        _unary_key,
        _binary_key,
        _BOOLEAN_KEYS,
        extra_args=(LegionSteps(model),),
    )
