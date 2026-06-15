from typing import Any, Dict

from model_checker.algorithms.explicit.TCTL.tctl_model_checking import (
    timed_model_checking,
)


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Run TCTL model checking."""
    try:
        raw_result = timed_model_checking(formula, filename)

        # TCTL returns a dict with 'res' and 'initial_state'
        # We ensure it matches VMI expectations
        res_str = raw_result.get("res", "")
        if not res_str.startswith("Result:"):
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
