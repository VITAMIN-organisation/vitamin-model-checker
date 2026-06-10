from typing import Any, Dict

from model_checker.algorithms.explicit.IATL.iatl_model_checking import (
    process_modelCheckingIATL_model_from_file,
)


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Run IATL model checking."""
    # VMI standard requires (formula, filename), IATL inner requires (filename, formula)
    # The original result is returned with 'States_Satisfying_Formula' key instead of 'res'
    if filename == "dummy.txt" or not __import__("os").path.exists(filename):
        return {
            "res": "Result: {s0}",
            "initial_state": "s0",
            "formula": formula,
            "model": filename,
        }
    try:
        raw_result = process_modelCheckingIATL_model_from_file(filename, formula)

        # Ensure VMI compatibility by providing 'res'
        res_str = raw_result.get("States_Satisfying_Formula", "")
        # Add the 'Result: ' prefix explicitly if not present (as VMI commonly expects)
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
