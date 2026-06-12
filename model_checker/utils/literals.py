"""Parse literal values embedded in formula trees and checker results."""

import ast
from typing import List, Optional, Set, Tuple, Union


def parse_state_set_literal(value: Optional[Union[str, Set[str]]]) -> Set[str]:
    """Parse a state set from a set, tuple string, or tree node value."""
    if value is None or value == "":
        return set()
    if isinstance(value, set):
        return {str(s) for s in value}
    if value in ("set()", "{}"):
        return set()

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, set):
            return {str(item).strip("'\"") for item in parsed}
        if isinstance(parsed, (list, tuple)):
            return {str(item).strip("'\"") for item in parsed}
    except (ValueError, SyntaxError, TypeError):
        pass

    return set()


def parse_tuple_list_literal(value: str) -> List[Tuple[str, float]]:
    """Parse a list of (state, value) pairs from a string; return [] on failure."""
    if value in ("[]", None, ""):
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (list, tuple)):
            result: List[Tuple[str, float]] = []
            for item in parsed:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    state, val = item
                    result.append((str(state), float(val)))
            return result
    except (ValueError, SyntaxError, TypeError):
        return []
    return []
