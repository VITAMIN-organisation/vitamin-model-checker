"""Model-checking result formatting."""

from typing import Any, Callable, Dict, Optional, Set, Union

from model_checker.algorithms.explicit.shared.verification_result import (
    VerificationResult,
)
from model_checker.utils.literals import parse_state_set_literal


def verify_initial_state(
    initial_state: str, result_value: Union[str, Set[str]]
) -> bool:
    """True if initial_state is in the result set."""
    states = {str(s) for s in parse_state_set_literal(result_value)}
    return initial_state in states


def format_model_checking_result(
    result_states: Union[str, Set[str]],
    initial_state: str,
    is_satisfied: bool,
) -> Dict[str, Any]:
    """Legacy res / initial_state dict."""
    if isinstance(result_states, set):
        result_states = str({str(s) for s in result_states})
    return {
        "res": f"Result: {result_states}",
        "initial_state": f"Initial state {initial_state}: {is_satisfied}",
    }


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
        "raw_result": raw_result,
    }


def run_explicit_entry_model_checking(
    check_fn: Callable[[str, str], Dict[str, Any]],
    formula: str,
    filename: str,
) -> Dict[str, Any]:
    """Call check_fn and wrap errors for TCTL/TOL entry points."""
    try:
        return wrap_explicit_entry_result(
            check_fn(formula, filename), formula, filename
        )
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {"error": {"message": str(exc), "type": type(exc).__name__}}


def create_verification_result(
    states: Set[str],
    initial_state: str,
    trace: Optional[Any] = None,
    strategy: Optional[Any] = None,
    **metadata: Any,
) -> VerificationResult:
    """VerificationResult from a state set."""
    satisfied = initial_state in states
    return VerificationResult(
        states=states,
        satisfied=satisfied,
        initial_state=initial_state,
        trace=trace,
        strategy=strategy,
        metadata=metadata,
    )


def format_verification_result(
    result: VerificationResult,
    include_trace: bool = True,
    compact_format: bool = False,
) -> Dict[str, Any]:
    """VerificationResult as an API dict."""
    if compact_format:
        return result.to_compact_dict()

    if include_trace:
        return result.to_dict()

    return {
        "res": f"Result: {result.states}",
        "initial_state": f"Initial state {result.initial_state}: {result.satisfied}",
        "satisfied": result.satisfied,
        "states": sorted(result.states),
    }
