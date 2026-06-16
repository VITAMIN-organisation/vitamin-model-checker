"""Entry-point result wrappers for explicit algorithms."""

from typing import Any, Callable, Dict

from model_checker.utils.error_handler import create_system_error


def wrap_explicit_entry_result(
    raw_result: Dict[str, Any],
    formula: str,
    filename: str,
) -> Dict[str, Any]:
    """Add formula and model fields for VMI callers."""
    res_str = raw_result.get("res", "")
    if not res_str.startswith("Result"):
        res_str = f"Result: {res_str}"
    return {
        "res": res_str,
        "initial_state": raw_result.get("initial_state", ""),
        "formula": formula,
        "model": filename,
    }


def run_explicit_entry_model_checking(
    check_fn: Callable[[str, str], Dict[str, Any]],
    formula: str,
    filename: str,
) -> Dict[str, Any]:
    """Call check_fn and wrap errors for explicit entry points."""
    try:
        return wrap_explicit_entry_result(
            check_fn(formula, filename), formula, filename
        )
    except Exception as exc:
        return create_system_error(f"Error during model checking: {str(exc)}")
