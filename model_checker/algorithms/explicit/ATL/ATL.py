"""
ATL Model Checker.

This module implements model checking for ATL formulas over Concurrent Game Structures.
ATL extends CTL with coalition modalities: <A>phi means "coalition A has a strategy
to ensure phi holds regardless of opponent actions."

Key Algorithm:
- Tree-based model checking: parse formula into tree, evaluate bottom-up
- Coalition pre-image (pre): compute states where coalition can force next transition
- Fixpoint computation for temporal operators (F, G, U)

Why ATL over CTL:
- CTL's path quantifiers (E, A) are for single-agent systems
- ATL's coalition operators handle multi-agent strategic settings
- Coalition semantics: <A>phi holds if A can guarantee phi against any opponent behavior
"""

from typing import TYPE_CHECKING, Any, Dict

from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
)
from model_checker.algorithms.explicit.ATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    resolve_atom_with_constants,
    verify_initial_state,
)
from model_checker.engine.runner import build_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _get_parser():
    return FormulaParserFactory.get_parser_instance("ATL")


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def _core_atl_checking(cgs: "CGS", formula: str) -> Dict[str, Any]:
    """
    Core ATL model checking logic.

    Args:
        cgs: Model parser instance (already loaded)
        formula: ATL formula string

    Returns:
        Dictionary with result or error information
    """
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_formula_tree(
        res_parsing,
        lambda atom: resolve_atom_with_constants(cgs, atom, parser),
    )
    if root is None:
        return create_semantic_error("The atom does not exist")

    transition_cache = build_transition_cache(cgs)

    solve_tree(cgs, root, transition_cache)
    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """
    Execute model checking for ATL formula.

    This is the main entry point for ATL model checking, following
    the common wrapper pattern for consistent error handling.

    Args:
        formula: ATL formula string
        filename: Path to model file

    Returns:
        Dictionary with keys:
        - "res": Result string (e.g., "Result: {s0, s1}")
        - "initial_state": Initial state verification string
        - "error": (optional) Structured error information
    """
    from model_checker.engine.runner import (
        execute_model_checking_with_parser,
    )

    return execute_model_checking_with_parser(
        formula, filename, "ATL", _core_atl_checking
    )
