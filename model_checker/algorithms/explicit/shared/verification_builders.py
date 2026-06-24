"""Builders for structured verification results."""

from typing import Any

from model_checker.algorithms.explicit.shared.verification_result import (
    VerificationResult,
)


def create_verification_result(
    states: set[str],
    initial_state: str,
    trace: Any | None = None,
    strategy: Any | None = None,
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
