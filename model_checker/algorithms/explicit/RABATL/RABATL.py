"""
RABATL (Resource-Aware Bounded ATL) Model Checker.

This module implements model checking for RABATL formulas over cost-CGS models.
RABATL is similar to RBATL but with resource-aware cost computation that
considers coalition-specific resource consumption.
"""

from model_checker.algorithms.explicit.RABATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    normalize_state_set,
)
from model_checker.engine.runner import (
    build_formula_tree,
    states_where_prop_holds,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _get_parser():
    return FormulaParserFactory.get_parser_instance("RABATL")


def build_tree(cgs, tpl):
    """
    Build formula tree with atom resolution for RABATL model checking.
    """
    return build_formula_tree(
        tpl,
        lambda atom: _resolve_atom(cgs, atom),
    )


def _resolve_atom(cgs, atom):
    """
    Resolve atomic proposition into set of state names.
    """
    states = states_where_prop_holds(cgs, str(atom))
    if states is None:
        return None
    return normalize_state_set(states)


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def _core_rabatl_checking(cgs, formula):
    """Core RABATL model checking logic."""
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("Atomic proposition not found in model")

    solve_tree(cgs, root)

    initial_state = cgs.initial_state
    states_set = normalize_state_set(root.value)
    is_satisfied = initial_state in states_set

    return format_model_checking_result(root.value, initial_state, is_satisfied)


def model_checking(formula, filename):
    """Main entry for RABATL."""
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
        formula, filename, "RABATL", _core_rabatl_checking
    )
