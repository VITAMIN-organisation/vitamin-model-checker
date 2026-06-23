"""Formula tree solver for COTL model checking."""

from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import cgs_actions

from .operators import (
    handle_coalition_eventually,
    handle_coalition_globally,
    handle_coalition_next,
    handle_coalition_release,
    handle_coalition_until,
    handle_coalition_weak,
)

_UNARY = {
    "NOT": lambda cgs, node, _ctx: handle_not(cgs, node),
    "GLOBALLY": handle_coalition_globally,
    "NEXT": handle_coalition_next,
    "EVENTUALLY": handle_coalition_eventually,
}
_BINARY = {
    "OR": lambda cgs, node, _ctx: handle_or(cgs, node),
    "AND": lambda cgs, node, _ctx: handle_and(cgs, node),
    "IMPLIES": lambda cgs, node, _ctx: handle_implies(cgs, node),
    "UNTIL": handle_coalition_until,
    "RELEASE": handle_coalition_release,
    "WEAK": handle_coalition_weak,
}


def _cotl_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("COALITION_DEMONIC", val):
        if parser_instance.verify("GLOBALLY", val):
            return "GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "EVENTUALLY"
    return None


def _cotl_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("COALITION_DEMONIC", val):
        if parser_instance.verify("UNTIL", val):
            return "UNTIL"
        if parser_instance.verify("RELEASE", val):
            return "RELEASE"
        if parser_instance.verify("WEAK", val):
            return "WEAK"
    return None


def solve_tree(cgs, node, solve_context):
    """Recursively solve the COTL formula tree bottom-up."""
    if node.left is not None:
        solve_tree(cgs, node.left, solve_context)
    if node.right is not None:
        solve_tree(cgs, node.right, solve_context)

    parser = FormulaParserFactory.get_parser_instance("COTL")
    if node.right is None:
        key = _cotl_unary_key(parser, node.value)
        if key and key in _UNARY:
            _UNARY[key](cgs, node, solve_context)
    elif node.left is not None and node.right is not None:
        key = _cotl_binary_key(parser, node.value)
        if key and key in _BINARY:
            _BINARY[key](cgs, node, solve_context)


def build_solve_context(graph):
    """Build solve context with pre-image cache and coalition agent lookup."""
    from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
        build_pre_by_index,
    )

    num_states = len(graph)
    return {
        "graph": graph,
        "pre_by_index": build_pre_by_index(graph),
        "all_states_index": set(range(num_states)),
        "agents_set_for": cgs_actions.get_agents_from_coalition,
    }
