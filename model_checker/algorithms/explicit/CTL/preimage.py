"""Pre-image computation for CTL (EX, AX)."""

from typing import Any

# Below this edge count, a linear scan is faster than building a reverse-index dict.
_SMALL_GRAPH_THRESHOLD = 50


def _build_reverse_index(
    transitions: list[tuple[Any, Any]],
) -> dict[str, set[str]]:
    """Build reverse index: target -> set of source states."""
    reverse_index: dict[str, set[str]] = {}
    for source, target in transitions:
        target_str = str(target)
        if target_str not in reverse_index:
            reverse_index[target_str] = set()
        reverse_index[target_str].add(str(source))
    return reverse_index


def pre_image_exist(
    transitions: list[tuple[Any, Any]],
    target_states: set[str],
    reverse_index: dict[str, set[str]] | None = None,
) -> set[str]:
    """Existential pre-image (EX): states with at least one successor in target_states."""
    target_states = {str(s) for s in target_states}

    if len(transitions) < _SMALL_GRAPH_THRESHOLD and reverse_index is None:
        predecessors = set()
        target_strs = {str(s) for s in target_states}
        for source, target in transitions:
            if str(target) in target_strs:
                predecessors.add(str(source))
        return predecessors

    if reverse_index is None:
        reverse_index = _build_reverse_index(transitions)
    predecessors = set()
    for state in target_states:
        state_str = str(state)
        if state_str in reverse_index:
            predecessors.update(reverse_index[state_str])
    return predecessors


def pre_image_all(
    transitions: list[tuple[Any, Any]],
    all_states: set[str],
    target_states: set[str],
) -> set[str]:
    """Universal pre-image (AX): states whose successors are all in target_states.

    Models must be total (every state has a successor); validated on load.
    """
    all_states = {str(s) for s in all_states}
    target_states = {str(s) for s in target_states}

    forward_index = {}
    for source, target in transitions:
        source_str = str(source)
        if source_str not in forward_index:
            forward_index[source_str] = set()
        forward_index[source_str].add(str(target))

    result = set()
    for state in all_states:
        state_str = str(state)
        successors = forward_index.get(state_str, set())
        if successors and successors.issubset(target_states):
            result.add(state_str)

    return result
