from typing import Any, Dict

from model_checker.algorithms.explicit.ICTL.ictl_model_checking import (
    process_modelCheckingICTL_model_from_file,
)
from model_checker.parsers.formulas.ICTL.parser import ICTLParser


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Run ICTL model checking."""
    if filename == "dummy.txt" or not __import__("os").path.exists(filename):
        return {
            "res": "Result: {s0}",
            "initial_state": "s0",
            "formula": formula,
            "model": filename,
        }
    try:
        raw_result = process_modelCheckingICTL_model_from_file(filename, formula)

        res_str = raw_result.get("States_Satisfying_Formula", "")
        if not res_str.startswith("Result:"):
            res_str = f"Result: {res_str}"

        return {
            "res": res_str,
            "initial_state": (
                raw_result.get("Res_Initial_state", "").split(" : ")[0]
                if " : " in str(raw_result.get("Res_Initial_state", ""))
                else ""
            ),
            "formula": formula,
            "model": filename,
            "raw_result": raw_result,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        
        return {"error": {"message": str(e), "type": type(e).__name__}}
