"""Shared boolean set semantics for explicit algorithms."""

from typing import Optional, Set


def compute_boolean_result(
    operator_name: str,
    left_states: Set[str],
    right_states: Optional[Set[str]] = None,
    all_states: Optional[Set[str]] = None,
) -> Set[str]:
    """Evaluate boolean operator semantics over state sets."""
    if operator_name == "NOT":
        if all_states is None:
            raise ValueError("NOT requires all_states.")
        return all_states - left_states

    if right_states is None:
        raise ValueError(f"{operator_name} requires right_states.")

    if operator_name == "OR":
        return left_states | right_states
    if operator_name == "AND":
        return left_states & right_states
    if operator_name == "IMPLIES":
        if all_states is None:
            raise ValueError("IMPLIES requires all_states.")
        return (all_states - left_states) | right_states

    raise ValueError(f"Unsupported boolean operator: {operator_name}")
