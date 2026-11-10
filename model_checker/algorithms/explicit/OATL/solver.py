"""Bottom-up formula tree solver for OATL model checking."""

from model_checker.algorithms.explicit.OATL.operators import (
    PrefixReader,
    handle_eventually,
    handle_globally,
    handle_next,
    handle_release,
    handle_until,
    handle_weak_until,
)
from model_checker.algorithms.explicit.OATL.preimage import DemonicPreimage
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.algorithms.explicit.shared.cost_utils import (
    extract_coalition_and_cost,
)
from model_checker.algorithms.explicit.shared.solver_core import solve_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

_BOOLEAN_KEYS = {"NOT", "AND", "OR", "IMPLIES"}
_UNARY = {
    "NOT": handle_not,
    "NEXT": handle_next,
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
_TEMPORAL_UNARY = ("NEXT", "EVENTUALLY", "GLOBALLY")
_TEMPORAL_BINARY = ("UNTIL", "RELEASE", "WEAK")


def _operator_key(parser, value, prefix_token, boolean_keys, temporal_keys):
    for key in boolean_keys:
        if parser.verify(key, value):
            return key
    if parser.verify(prefix_token, value):
        for key in temporal_keys:
            if parser.verify(key, value):
                return key
    return None


def solve_demonic_tree(
    cgs, root, logic: str, prefix_token: str, read_prefix: PrefixReader
) -> None:
    """Solve a tree whose temporal operators carry a Demon prefix (OATL, and OL).

    `prefix_token` is the parser token of that prefix and `read_prefix` reads its
    coalition and budget.
    """

    def unary_key(parser, value):
        return _operator_key(parser, value, prefix_token, ("NOT",), _TEMPORAL_UNARY)

    def binary_key(parser, value):
        return _operator_key(
            parser, value, prefix_token, ("OR", "AND", "IMPLIES"), _TEMPORAL_BINARY
        )

    solve_formula_tree(
        cgs,
        root,
        FormulaParserFactory.get_parser_instance(logic),
        _UNARY,
        _BINARY,
        unary_key,
        binary_key,
        _BOOLEAN_KEYS,
        extra_args=(DemonicPreimage(cgs), read_prefix),
        cache={},
    )


def solve_tree(cgs, root) -> None:
    """Replace each node value with the set of states satisfying its subformula."""
    solve_demonic_tree(
        cgs, root, "OATL", "COALITION_DEMONIC", extract_coalition_and_cost
    )
