"""
OATL Model Checker.

This module implements model checking for OATL formulas over cost-CGS models.
OATL extends ATL with cost bounds and one-sided strategies: <J><n> means
"coalition J can achieve the goal with cost at most n."
"""

import logging

from model_checker.algorithms.explicit.OATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    resolve_atom_with_constants,
)
from model_checker.engine.runner import (
    build_formula_tree,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

logger = logging.getLogger(__name__)


def _get_parser():
    return FormulaParserFactory.get_parser_instance("OATL")


def build_tree(cgs, tpl):
    """Build formula tree with atom resolution for OATL model checking."""
    parser = _get_parser()
    return build_formula_tree(
        tpl,
        lambda atom: resolve_atom_with_constants(cgs, atom, parser),
    )


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def _core_oatl_checking(cgs, formula):
    """Core OATL logic."""
    from model_checker.algorithms.explicit.OATL.preimage import (
        _base_action_cache,
        _cost_cache,
    )
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    _cost_cache.clear()
    _base_action_cache.clear()

    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("One or more atoms do not exist in the model")

    solve_tree(cgs, root)

    from model_checker.algorithms.explicit.shared.result_utils import (
        verify_initial_state,
    )

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


def model_checking(formula, filename):
    """Main entry point for OATL."""
    from model_checker.algorithms.explicit.ATL import (
        model_checking as atl_model_checking,
    )
    from model_checker.algorithms.explicit.shared.resource_bounded_to_atl import (
        resource_bounded_atl_to_atl,
    )
    from model_checker.engine.runner import (
        execute_model_checking_with_parser,
    )

    atl_formula = resource_bounded_atl_to_atl(formula)
    atl_result = atl_model_checking(atl_formula, filename)
    if "error" in atl_result:
        return atl_result
    if str(atl_result.get("initial_state", "")).endswith(": False"):
        return atl_result

    return execute_model_checking_with_parser(
        formula, filename, "OATL", _core_oatl_checking
    )
