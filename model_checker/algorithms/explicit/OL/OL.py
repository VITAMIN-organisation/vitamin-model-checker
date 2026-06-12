"""OL model checking on cost-bounded game structures."""

import logging

from model_checker.algorithms.explicit.OL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)

logger = logging.getLogger(__name__)


def _core_ol_checking(cgs, formula):
    """Run OL model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("OL")
    res_parsing = parser.parse(formula)
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return create_semantic_error("One or more atoms do not exist in the model")

    solve_tree(cgs, root)

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry("OL", _core_ol_checking)
