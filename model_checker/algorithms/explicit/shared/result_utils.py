"""Format model-checking results and check the initial state."""

from typing import Any, Dict, Optional, Set, Union

from model_checker.algorithms.explicit.shared.verification_result import (
    VerificationResult,
)
from model_checker.utils.literals import parse_state_set_literal


def verify_initial_state(
    initial_state: str, result_value: Union[str, Set[str]]
) -> bool:
    """Return True when the initial state is in the result set."""
    states = {str(s) for s in parse_state_set_literal(result_value)}
    return initial_state in states


def format_model_checking_result(
    result_states: Union[str, Set[str]],
    initial_state: str,
    is_satisfied: bool,
) -> Dict[str, Any]:
    """Build the standard result dict with ``res`` and ``initial_state`` keys."""
    if isinstance(result_states, set):
        result_states = str({str(s) for s in result_states})
    return {
        "res": "Result: " + result_states,
        "initial_state": f"Initial state {initial_state}: {is_satisfied}",
    }


def create_verification_result(
    states: Set[str],
    initial_state: str,
    trace: Optional[Any] = None,
    strategy: Optional[Any] = None,
    **metadata: Any,
) -> VerificationResult:
    """Create a VerificationResult, optionally with a trace or strategy."""
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
    """Turn a VerificationResult into a dict for API output."""
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
