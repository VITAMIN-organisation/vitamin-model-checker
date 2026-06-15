"""ICTL model checking on birelational CGS models."""

from typing import Any, Dict

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.solver import solve_tree
from model_checker.algorithms.explicit.ICTL.util.generators import (
    generate_experiment_model,
)
from model_checker.algorithms.explicit.ICTL.util.graph import read_file
from model_checker.algorithms.explicit.shared.result_utils import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.parsers.formulas.ICTL.ictl_ply_parser import do_parsingICTL
from model_checker.utils.literals import parse_state_set_literal


def run_model_checking(formula: str, checker: ICTLModelChecker) -> Dict[str, Any]:
    """Parse formula, evaluate on checker, return legacy result dict."""
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
    formatted = format_model_checking_result(root.value, init_state, is_satisfied)
    states_str = formatted["res"].removeprefix("Result: ")

    return {
        "States_Satisfying_Formula": states_str,
        "Tot_states": len(parse_state_set_literal(states_str)),
        "Res_Initial_state": f"{init_state} : {is_satisfied}",
    }


def process_model_checking_from_file(filename: str, formula: str) -> Dict[str, Any]:
    """Load an ICTL model file and run model checking."""
    data = read_file(filename)
    return run_model_checking(formula, ICTLModelChecker(data))


def process_model_checking_generated(
    states_row: int, states_col: int, formula: str
) -> Dict[str, Any]:
    """Run model checking on a synthetic experiment model."""
    data = generate_experiment_model(states_row, states_col)
    return run_model_checking(formula, ICTLModelChecker(data))


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """VMI entry point for ICTL model checking."""
    try:
        raw_result = process_model_checking_from_file(filename, formula)
        res_str = raw_result.get("States_Satisfying_Formula", "")
        if not res_str.startswith("Result:"):
            res_str = f"Result: {res_str}"

        init_field = str(raw_result.get("Res_Initial_state", ""))
        init_state = init_field.split(" : ")[0] if " : " in init_field else ""

        return {
            "res": res_str,
            "initial_state": init_state,
            "formula": formula,
            "model": filename,
            "raw_result": raw_result,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": {"message": str(e), "type": type(e).__name__}}
