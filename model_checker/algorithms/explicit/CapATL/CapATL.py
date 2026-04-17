"""
CapATL (Capacity ATL) Model Checker.

This module implements model checking for CapATL formulas over cap-CGS models.
CapATL extends ATL with explicit capacities for agents and knowledge-based reasoning.

Key Concepts:
- Capacity constraints: Agents have explicit capacity sets (e.g., "1c" means agent 1 has capacity c)
- Knowledge-based reasoning: Agents reason about what they know based on their capacities
- Pointed knowledge: State-knowledge pairs (Sigma, Delta) representing epistemic states
- Coalition operators: <A>phi means coalition A can ensure phi using their capacities

Algorithm:
- Tree-based model checking: parse formula into tree, evaluate bottom-up
- Knowledge pre-image: compute predecessor states with knowledge updates
- Fixpoint computation: Least (EVENTUALLY), Greatest (GLOBALLY)
"""

from typing import Any, Dict

from model_checker.algorithms.explicit.CapATL.solver import (
    build_tree,
    solve_tree,
)
from model_checker.algorithms.explicit.CapATL.utils import (
    Omega_Y,
    X_agt_cap,
    X_agt_cap2,
    build_state_cache,
    function_F_for_succ,
    indistinguishable_action,
    succ,
)
from model_checker.algorithms.explicit.shared.result_utils import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.runner import execute_model_checking_with_parser
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _get_parser():
    return FormulaParserFactory.get_parser_instance("CapATL")


def _validate_capatl_model(cgs):
    """Validate CapATL model structure."""
    if hasattr(cgs, "validity_model") and cgs.validity_model() is False:
        from model_checker.utils.error_handler import create_model_error

        return create_model_error("Incorrect model structure")
    return None


def _core_capatl_checking(cgs, formula):
    """
    Core CapATL model checking logic.

    Args:
        cgs: Model parser instance (already loaded)
        formula: CapATL formula string

    Returns:
        Dictionary with result or error information
    """
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    # Parse the CapATL formula
    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    build_state_cache(cgs)

    # Build formula tree, resolving atoms and capacities to pointed knowledge sets
    root = build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error(
            "One or more atoms or capacities do not exist in the model"
        )

    # Evaluate the formula tree
    solve_tree(cgs, root)

    # Extract winning states from pointed knowledge set
    winning_states = set()
    for pk in root.value:
        winning_states.add(str(pk.state))

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, winning_states)
    return format_model_checking_result(winning_states, initial_state, is_satisfied)


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """
    Execute model checking for CapATL formula.

    This is the main entry point for CapATL model checking, following
    the common wrapper pattern for consistent error handling.

    Args:
        formula: CapATL formula string
        filename: Path to model file

    Returns:
        Dictionary with keys:
        - "res": Result string (e.g., "Result: ['s0', 's1']")
        - "error": (optional) Structured error information
    """
    X_agt_cap.cache_clear()
    X_agt_cap2.cache_clear()
    indistinguishable_action.cache_clear()
    function_F_for_succ.cache_clear()
    succ.cache_clear()
    Omega_Y.cache_clear()

    return execute_model_checking_with_parser(
        formula,
        filename,
        "CapATL",
        _core_capatl_checking,
        pre_validation_func=_validate_capatl_model,
    )
