"""Pre-image helpers for ICTL (EX / AX over transition edges)."""


def pre_image_exist(
    transitions: list[tuple[str, str]], target_states: set[str]
) -> set[str]:
    """Existential pre-image: states with at least one successor in target_states."""
    target_states = {str(s) for s in target_states}
    return {s for s, t in transitions if t in target_states}


def pre_image_all(
    transitions: list[tuple[str, str]], target_states: set[str]
) -> set[str]:
    """Universal pre-image: states whose successors are all in target_states."""
    target_states = {str(s) for s in target_states}
    result: set[str] = set()
    for state in target_states:
        for predecessor in {s for s, t in transitions if t == state}:
            successors = {t for s, t in transitions if s == predecessor}
            if successors.issubset(target_states):
                result.add(predecessor)
    return result
