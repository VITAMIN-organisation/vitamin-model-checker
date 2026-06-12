"""IATL model checking on BCGS models."""

from typing import Any, Dict

from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
from model_checker.algorithms.explicit.IATL.solver import solve_tree
from model_checker.algorithms.explicit.shared.result_utils import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_semantic_error, create_syntax_error


def _core_iatl_checking(parser, formula: str) -> Dict[str, Any]:
    """Run IATL model checking on a loaded BCGS parser."""
    checker = IATLModelChecker(parser.data)

    formula_parser = FormulaParserFactory.get_parser_instance("IATL")
    parsed = formula_parser.parse(formula, n_agent=checker.data["number_of_agents"])
    if parsed is None:
        error_msg = (
            formula_parser.errors[0]
            if formula_parser.errors
            else "Syntax error in formula"
        )
        return create_syntax_error(error_msg)

    root = checker.build_tree(parsed)
    if root is None:
        return create_semantic_error("Syntax Error: the atom does not exist")

    solve_tree(checker, root)
    init_state = str(checker.data["initial_state"])
    is_satisfied = verify_initial_state(init_state, root.value)
    return format_model_checking_result(root.value, init_state, is_satisfied)


model_checking = create_model_checking_entry("IATL", _core_iatl_checking)
