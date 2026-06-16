"""ICTL model checking on birelational CGS models."""

from functools import partial
from typing import Any, Dict

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.solver import solve_tree
from model_checker.algorithms.explicit.ICTL.util.graph import read_file
from model_checker.algorithms.explicit.shared.entry_result_wrappers import (
    run_explicit_entry_model_checking,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.parsers.formulas.ICTL.ictl_ply_parser import do_parsingICTL


def run_model_checking(formula: str, checker: ICTLModelChecker) -> Dict[str, Any]:
    """Parse formula, evaluate on checker, return standard result dict."""
    if not formula.strip():
        return {"res": "Error: formula not entered", "initial_state": ""}

    parsed = do_parsingICTL(formula)
    if parsed is None:
        return {"res": "Syntax Error", "initial_state": ""}

    root = checker.build_tree(parsed)
    if root is None:
        return {"res": "Syntax Error: the atom does not exist", "initial_state": ""}

    solve_tree(checker, root)

    init_state = str(checker.data["initial_state"])
    is_satisfied = verify_initial_state(init_state, root.value)
    return format_model_checking_result(root.value, init_state, is_satisfied)


model_checking = partial(
    run_explicit_entry_model_checking,
    lambda formula, filename: run_model_checking(
        formula, ICTLModelChecker(read_file(filename))
    ),
)
