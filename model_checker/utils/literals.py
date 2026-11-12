"""Parse literal values embedded in formula trees and checker results."""

import ast
import re
from collections.abc import Iterable
from typing import Any

_DIGITS = re.compile(r"(\d+)")


def _natural_key(name: str) -> list[str | int]:
    # re.split with a group puts text at even and numbers at odd positions, so
    # two keys always compare text with text and number with number.
    return [int(part) if i % 2 else part for i, part in enumerate(_DIGITS.split(name))]


def state_set_literal(states: Iterable[Any]) -> str:
    """A state set as the tuple every result prints, in natural order
    ("('s1', 's2', 's10')"); `parse_state_set_literal` reads it back."""
    return str(tuple(sorted({str(s) for s in states}, key=_natural_key)))


def parse_state_set_literal(value: str | set[str] | None) -> set[str]:
    """Parse a state set from a set, tuple string, or tree node value.

    Raises ValueError for a string that is not a set, list or tuple literal.
    """
    if value is None or value == "":
        return set()
    if isinstance(value, set):
        return {str(s) for s in value}
    # `{}` reads as a dict, but a result prints the empty set that way.
    if value == "{}":
        return set()

    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError) as e:
        raise ValueError(f"Not a state set literal: {value!r}") from e
    if not isinstance(parsed, (set, list, tuple)):
        raise ValueError(f"Not a state set literal: {value!r}")
    return {str(item).strip("'\"") for item in parsed}


def parse_tuple_list_literal(value: str) -> list[tuple[str, float]]:
    """Parse a list of (state, value) pairs from a string; return [] on failure."""
    if value in ("[]", None, ""):
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (list, tuple)):
            result: list[tuple[str, float]] = []
            for item in parsed:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    state, val = item
                    result.append((str(state), float(val)))
            return result
    except (ValueError, SyntaxError, TypeError):
        return []
    return []
