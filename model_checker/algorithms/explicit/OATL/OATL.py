"""
OATL Model Checker.

This module implements model checking for OATL formulas over cost-CGS models.
OATL extends ATL with cost bounds and one-sided strategies: <J><n> means
"coalition J can achieve the goal with cost at most n."
"""

import logging

from model_checker.algorithms.explicit.OATL.preimage import (
    _base_action_cache,
    _cost_cache,
)
from model_checker.algorithms.explicit.OATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    build_pre_by_index,
)
from model_checker.engine.atl_prefilter import run_atl_prefilter
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)

logger = logging.getLogger(__name__)


def _core_oatl_checking(cgs, formula):
    """Core OATL logic."""
    _cost_cache.clear()
    _base_action_cache.clear()

    parser = FormulaParserFactory.get_parser_instance("OATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return create_semantic_error("One or more atoms do not exist in the model")

    solve_context = {
        "graph": cgs.graph,
        "pre_by_index": build_pre_by_index(cgs.graph),
    }
    solve_tree(cgs, root, solve_context)

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry(
    "OATL", _core_oatl_checking, prefilter_func=run_atl_prefilter
)
