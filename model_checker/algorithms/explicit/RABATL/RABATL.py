"""
RABATL (Resource-Aware Bounded ATL) Model Checker.

This module implements model checking for RABATL formulas over cost-CGS models.
RABATL is similar to RBATL but with resource-aware cost computation that
considers coalition-specific resource consumption.
"""

from model_checker.algorithms.explicit.RABATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
)
from model_checker.engine.atl_prefilter import run_atl_prefilter
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)


def _core_rabatl_checking(cgs, formula):
    """Core RABATL model checking logic."""
    parser = FormulaParserFactory.get_parser_instance("RABATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("Atomic proposition not found in model")

    solve_tree(cgs, root)

    initial_state = cgs.initial_state
    states_set = {str(s) for s in root.value}
    is_satisfied = initial_state in states_set

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry(
    "RABATL", _core_rabatl_checking, prefilter_func=run_atl_prefilter
)
