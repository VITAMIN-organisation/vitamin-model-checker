"""COTL model checker over costCGS models."""

from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.shared.atom_utils import (
    build_resolved_formula_tree,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)

from .solver import build_solve_context, solve_tree


def _reset_cotl_caches(cgs):
    if not hasattr(cgs, "_cost_cache"):
        cgs._cost_cache = {}
    else:
        cgs._cost_cache.clear()
    if not hasattr(cgs, "_base_action_cache"):
        cgs._base_action_cache = {}
    else:
        cgs._base_action_cache.clear()


def _core_cotl_checking(cgs, formula):
    _reset_cotl_caches(cgs)
    parser = FormulaParserFactory.get_parser_instance("COTL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return create_semantic_error("The atom does not exist in the model")

    solve_context = build_solve_context(cgs.graph)
    solve_tree(cgs, root, solve_context)

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)
    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry("COTL", _core_cotl_checking)
