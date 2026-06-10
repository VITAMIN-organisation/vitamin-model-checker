"""
RBATL (Resource-Bounded ATL) Model Checker.

This module implements model checking for RBATL formulas over cost-CGS models.
RBATL extends ATL with resource bounds: <J><b> means "coalition J can achieve
the goal using at most b units of each resource."

Key Concepts:
- Multiple resource types (vector bounds instead of scalar)
- Per-step resource consumption
- Bound propagation through fixpoint iterations
"""

import logging

from model_checker.algorithms.explicit.RBATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
)
from model_checker.engine.runner import bind_resource_bounded_model_checking
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

logger = logging.getLogger(__name__)


def _core_rbatl_checking(cgs, formula):
    """Core RBATL model checking logic avoiding global variables."""
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = FormulaParserFactory.get_parser_instance("RBATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error(
            "One or more atomic propositions do not exist in the model"
        )

    solve_tree(cgs, root)

    initial_state = cgs.initial_state
    states_set = {str(s) for s in root.value}
    is_satisfied = initial_state in states_set

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = bind_resource_bounded_model_checking("RBATL", _core_rbatl_checking)
