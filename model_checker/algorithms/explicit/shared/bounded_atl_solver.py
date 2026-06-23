"""Formula tree solver and entry-point helper shared by RABATL and RBATL."""

from model_checker.algorithms.explicit.shared.atom_utils import (
    build_resolved_formula_tree,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.algorithms.explicit.shared.bounded_atl_operators import (
    handle_coalition_eventually,
    handle_coalition_globally,
    handle_coalition_next,
    handle_coalition_until,
)
from model_checker.algorithms.explicit.shared.bounded_atl_preimage import CostFilter
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_semantic_error, create_syntax_error

_COALITION_UNARY_KEYS = frozenset(
    {"COALITION_GLOBALLY", "COALITION_NEXT", "COALITION_EVENTUALLY"}
)

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


def _coalition_unary_key(parser_instance, val):
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("COALITION_BOUND", val):
        if parser_instance.verify("GLOBALLY", val):
            return "COALITION_GLOBALLY"
        if parser_instance.verify("NEXT", val):
            return "COALITION_NEXT"
        if parser_instance.verify("EVENTUALLY", val):
            return "COALITION_EVENTUALLY"
    return None


def _coalition_binary_key(parser_instance, val):
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("COALITION_BOUND", val) and parser_instance.verify(
        "UNTIL", val
    ):
        return "COALITION_UNTIL"
    return None


def solve_tree(cgs, node, cost_filter: CostFilter, logic: str, cache=None) -> None:
    """Recursively evaluate a resource-bounded ATL formula tree bottom-up."""
    if cache is None:
        cache = {}

    node_key = (
        str(node.value)
        + (str(node.left) if node.left else "")
        + (str(node.right) if node.right else "")
    )
    if node_key in cache:
        node.value = cache[node_key]
        return

    if node.left:
        solve_tree(cgs, node.left, cost_filter, logic, cache)
    if node.right:
        solve_tree(cgs, node.right, cost_filter, logic, cache)

    parser = FormulaParserFactory.get_parser_instance(logic)
    if node.right is None:
        key = _coalition_unary_key(parser, node.value)
        if key and key in _UNARY:
            if key in _COALITION_UNARY_KEYS:
                _UNARY[key](cgs, node, cost_filter)
            else:
                _UNARY[key](cgs, node)
    elif node.left and node.right:
        key = _coalition_binary_key(parser, node.value)
        if key and key in _BINARY:
            if key == "COALITION_UNTIL":
                _BINARY[key](cgs, node, cost_filter)
            else:
                _BINARY[key](cgs, node)

    cache[node_key] = node.value


def run_bounded_atl_checking(cgs, formula, cost_filter: CostFilter, logic: str):
    """Parse, solve, and format a resource-bounded ATL formula over a cost-CGS model."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("Atomic proposition not found in model")

    solve_tree(cgs, root, cost_filter=cost_filter, logic=logic)

    is_satisfied = verify_initial_state(cgs.initial_state, root.value)
    return format_model_checking_result(root.value, cgs.initial_state, is_satisfied)
