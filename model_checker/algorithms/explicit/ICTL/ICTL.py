"""ICTL model checking on birelational CGS models."""

from functools import partial
from typing import Any

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.solver import solve_tree
from model_checker.parsers.game_structures.birelational_matrix.birelational_matrix import (
    BirelationalMatrix,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _core_ictl_checking(parser: BirelationalMatrix, formula: str) -> dict[str, Any]:
    """Parse formula, evaluate on checker, return standard result dict."""
    checker = ICTLModelChecker(parser)

    formula_parser = FormulaParserFactory.get_parser_instance("ICTL")
    parsed = formula_parser.parse(formula)
    if parsed is None:
        err = formula_parser.errors[0] if formula_parser.errors else "Syntax Error"
        return {"res": err, "initial_state": ""}

    root = checker.build_tree(parsed)
    if root is None:
        return {"res": "Syntax Error: the atom does not exist", "initial_state": ""}

    solve_tree(checker, root)

    init_state = str(parser.initial_state)
    is_satisfied = verify_initial_state(init_state, root.value)
    return format_model_checking_result(root.value, init_state, is_satisfied)


model_checking = create_model_checking_entry("ICTL", _core_ictl_checking)
