"""
Bound vector utilities for resource-bounded logics (RABATL, RBATL).

Parses <J><b1,b2,...>Op and provides lexicographic increment/difference for bound vectors.
"""

from typing import List, Tuple


def inc_bound(current_bound: List[int], max_bound: List[int]) -> bool:
    """Increment current_bound lexicographically; return False when past max_bound."""
    for i in range(len(current_bound)):
        if max_bound[i] == 0:
            current_bound[i] = 0
            continue
        current_bound[i] += 1
        if current_bound[i] <= max_bound[i]:
            return True
        current_bound[i] = 0
    return False


def diff_bound(b1: List[int], b2: List[int]) -> List[int]:
    """Element-wise max(0, b1 - b2)."""
    return [max(0, x - y) for x, y in zip(b1, b2)]


def extract_coalition_and_bound(formula_node_value: str) -> Tuple[str, List[int]]:
    """Parse <J><b1,b2,...> into (coalition_str, [b1,b2,...]).

    Raises ValueError with a descriptive message when the format is invalid.
    """
    raw = formula_node_value.strip()
    if not raw.startswith("<"):
        raise ValueError(
            f"Invalid coalition-bound format '{formula_node_value}': expected string starting with '<'."
        )

    try:
        parts = raw[1:].split(">")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError("expected '<J><b1,b2,...>' with both coalition and bound.")

        coalition = parts[0]
        bound_part = parts[1]
        if not bound_part.startswith("<"):
            raise ValueError("bound part must start with '<', e.g. '<1,2>' or '<5>'.")
        if bound_part.endswith(">"):
            inner = bound_part[1:-1].strip()
        else:
            inner = bound_part[1:].strip()
        if not inner:
            raise ValueError("bound list cannot be empty.")

        bounds: List[int] = []
        for token in inner.split(","):
            token = token.strip()
            if not token:
                raise ValueError("empty bound value in list.")
            bounds.append(int(token))
    except ValueError as exc:
        raise ValueError(
            f"Invalid coalition-bound format '{formula_node_value}': {exc}"
        ) from exc

    return coalition, bounds
