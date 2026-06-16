"""Result verification and formatting helpers."""

from typing import Any, Dict, Set, Union

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
    """Standard res / initial_state dict."""
    if isinstance(result_states, set):
        result_states = str({str(s) for s in result_states})
    return {
        "res": f"Result: {result_states}",
        "initial_state": f"Initial state {initial_state}: {is_satisfied}",
    }


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
