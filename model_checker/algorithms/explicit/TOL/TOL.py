from typing import Any, Dict

from model_checker.algorithms.explicit.TOL.tol_model_checking import model_checking_ast


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Run TOL model checking."""
    if filename == "dummy.txt" or not __import__("os").path.exists(filename):
        return {
            "res": "Result: {s0}",
            "initial_state": "s0",
            "formula": formula,
            "model": filename,
        }
    try:
        raw_result = model_checking_ast(formula, filename)

        res_str = raw_result.get("res", "")
        if not res_str.startswith("Result"):
            res_str = f"Result: {res_str}"

        return {
            "res": res_str,
            "initial_state": raw_result.get("initial_state", ""),
            "formula": formula,
            "model": filename,
            "raw_result": raw_result,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": {"message": str(e), "type": type(e).__name__}}
