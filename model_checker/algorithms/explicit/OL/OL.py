"""
OL Model Checker.

This module implements model checking for OL formulas over cost-CGS models.
OL extends LTL with cost bounds and one-sided strategies; formulas use
a single bound, e.g. <k>F p for "p eventually holds within cost k."
"""

import logging

from model_checker.algorithms.explicit.OL.preimage import build_pre_set_array
from model_checker.algorithms.explicit.OL.solver import solve_tree
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
    return FormulaParserFactory.get_parser_instance("OL")


def build_tree(cgs, tpl):
    """Build formula tree with atom resolution for OL."""
    parser = _get_parser()
    return build_formula_tree(
        tpl,
        lambda atom: resolve_atom_with_constants(cgs, atom, parser),
    )


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def _core_ol_checking(cgs, formula):
    """Core OL model checking logic."""
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = _get_parser()
    res_parsing = parser.parse(formula)
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("One or more atoms do not exist in the model")

    pre_sets = build_pre_set_array(cgs)
    solve_tree(cgs, root, pre_sets)

    from model_checker.algorithms.explicit.shared.result_utils import (
        verify_initial_state,
    )

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


def model_checking(formula, filename):
    """Main entry for OL."""
    from model_checker.engine.runner import (
        execute_model_checking_with_parser,
    )

    return execute_model_checking_with_parser(
        formula, filename, "OL", _core_ol_checking
    )
