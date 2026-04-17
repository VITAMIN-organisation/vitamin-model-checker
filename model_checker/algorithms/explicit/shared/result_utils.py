"""
Shared result utilities for model checking algorithms.

This module provides common result-related operations used across multiple
logic implementations (ATL, CTL, LTL, NatATL, etc.) to avoid code duplication.

Key Design Decisions:
- verify_initial_state() checks if initial state satisfies the formula
- format_result() creates consistent result dictionaries across all logics
- New: Support for VerificationResult objects with witness/counterexample traces
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Union

from model_checker.algorithms.explicit.shared.state_utils import (
    normalize_state_set,
)
from model_checker.engine.runner import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.shared.verification_result import (
        VerificationResult,
    )


def verify_initial_state(
    initial_state: str, result_value: Union[str, Set[str]]
) -> bool:
    """
    Verify if the initial state is included in the result set.

    Args:
        initial_state: Name of the initial state (e.g., 's0')
        result_value: State set as a set or string (e.g. "{'s0', 's1'}")

    Returns:
        True if initial_state is in the state set, False otherwise.
    """
    states = normalize_state_set(parse_state_set_literal(result_value))
    return initial_state in states


def format_model_checking_result(
    result_states: Union[str, Set[str]],
    initial_state: str,
    is_satisfied: bool,
) -> Dict[str, Any]:
    """
    Format the model checking result into a standard dictionary.

    Args:
        result_states: States satisfying the formula (set or string representation)
        initial_state: Name of the initial state
        is_satisfied: Whether the initial state satisfies the formula

    Returns:
        Dictionary with 'res' and 'initial_state' keys in standard format.
    """
    if isinstance(result_states, set):
        result_states = str(normalize_state_set(result_states))
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
) -> "VerificationResult":
    """
    Create a VerificationResult object with states and optional trace/strategy.

    Args:
        states: Set of state names where the formula holds
        initial_state: Name of the initial state
        trace: Optional StateTrace object (witness or counterexample)
        strategy: Optional StrategyTrace object (for coalition operators)
        **metadata: Additional metadata to include in the result

    Returns:
        VerificationResult object
    """
    from model_checker.algorithms.explicit.shared.verification_result import (
        VerificationResult,
    )

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
    result: "VerificationResult",
    include_trace: bool = True,
    compact_format: bool = False,
) -> Dict[str, Any]:
    """
    Format a VerificationResult object into a dictionary for API responses.

    Args:
        result: VerificationResult object to format
        include_trace: Whether to include trace information in the output
        compact_format: If True, return only res and initial_state

    Returns:
        Dictionary with result information
    """
    if compact_format:
        return result.to_compact_dict()

    if include_trace:
        return result.to_dict()

    # Return without trace info
    return {
        "res": f"Result: {result.states}",
        "initial_state": f"Initial state {result.initial_state}: {result.satisfied}",
        "satisfied": result.satisfied,
        "states": sorted(result.states),
    }
