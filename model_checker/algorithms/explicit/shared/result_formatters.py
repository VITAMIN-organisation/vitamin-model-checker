"""Result verification and formatting helpers."""

from typing import Any

from model_checker.algorithms.explicit.shared.verification_result import (
    VerificationResult,
)
from model_checker.utils.literals import parse_state_set_literal, state_set_literal

_TAGGED_TYPES = frozenset({"semantic", "syntax", "model"})


def _raise_if_error(result: dict[str, Any], formula: str) -> None:
    """Re-raise an inner error, keeping its type as the tag value_error_to_response reads."""
    if "error" in result:
        error_type = result["error"]["type"]
        tag = f"[{error_type.upper()}] " if error_type in _TAGGED_TYPES else ""
        raise ValueError(
            f"{tag}Internal CTL check of '{formula}' failed: {result['error']['message']}"
        )


def states_of_result(result: dict[str, Any], formula: str) -> set[str]:
    """The states of a CTL result used inside another solver; an error raises instead of reading as no states."""
    _raise_if_error(result, formula)
    res = result["res"]
    if not res.startswith("Result: "):
        raise ValueError(f"Internal CTL check of '{formula}' returned {res!r}")
    return parse_state_set_literal(res.removeprefix("Result: "))


def initial_state_holds(result: dict[str, Any], formula: str) -> bool:
    """The initial-state verdict of a CTL result used inside another solver; an error raises instead of reading as False."""
    _raise_if_error(result, formula)
    return result["initial_state"].endswith(": True")


def verify_initial_state(initial_state: str, result_value: str | set[str]) -> bool:
    """True if initial_state is in the result set."""
    states = {str(s) for s in parse_state_set_literal(result_value)}
    return initial_state in states


def format_model_checking_result(
    result_states: str | set[str],
    initial_state: str,
    is_satisfied: bool,
) -> dict[str, Any]:
    """Standard res / initial_state dict; the states print as a sorted tuple."""
    if isinstance(result_states, str):
        result_states = parse_state_set_literal(result_states)
    states = state_set_literal(result_states)
    verdict = f"Initial state {initial_state}: {is_satisfied}" if initial_state else ""
    return {"res": f"Result: {states}", "initial_state": verdict}


def format_verification_result(
    result: VerificationResult,
    include_trace: bool = True,
    compact_format: bool = False,
) -> dict[str, Any]:
    """VerificationResult as an API dict."""
    if compact_format:
        return result.to_compact_dict()

    if include_trace:
        return result.to_dict()

    return {
        "res": f"Result: {state_set_literal(result.states)}",
        "initial_state": f"Initial state {result.initial_state}: {result.satisfied}",
        "satisfied": result.satisfied,
        "states": sorted(result.states),
    }
