"""Pre-image helpers for ICTL (EX / AX over transition edges)."""

from typing import List, Set, Tuple


def pre_image_exist(
    transitions: List[Tuple[str, str]], target_states: Set[str]
) -> Set[str]:
    """Existential pre-image: states with at least one successor in target_states."""
    target_states = {str(s) for s in target_states}
    return {s for s, t in transitions if t in target_states}


def pre_image_all(
    transitions: List[Tuple[str, str]], target_states: Set[str]
) -> Set[str]:
    """Universal pre-image: states whose successors are all in target_states."""
    target_states = {str(s) for s in target_states}
    result: Set[str] = set()
    for state in target_states:
        for predecessor in {s for s, t in transitions if t == state}:
            successors = {t for s, t in transitions if s == predecessor}
            if successors.issubset(target_states):
                result.add(predecessor)
    return result
