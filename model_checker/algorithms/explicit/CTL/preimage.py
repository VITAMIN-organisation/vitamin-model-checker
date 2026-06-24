"""Pre-image computation for CTL (EX, AX, Release) and predecessor tracking for traces."""

from typing import Any

from model_checker.parsers.game_structures.cgs import CGSProtocol


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

    if len(transitions) < 50 and reverse_index is None:
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

    States with no successors are included (vacuous case).
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
        if not successors or successors.issubset(target_states):
            result.add(state_str)

    return result


def pre_release_universal(
    cgs: CGSProtocol,
    phi_states: set[str],
    psi_states: set[str],
) -> set[str]:
    """Compute A(phi R psi) via greatest fixpoint (psi and (phi or AX Z))."""
    all_states = cgs.all_states_set
    phi_states = {str(s) for s in phi_states}
    psi_states = {str(s) for s in psi_states}

    result = psi_states.copy()
    transitions = cgs.get_edges()

    forward_index = {}
    for source, target in transitions:
        source_str = str(source)
        if source_str not in forward_index:
            forward_index[source_str] = set()
        forward_index[source_str].add(str(target))

    while True:
        new_result = set()
        for s in all_states:
            if s in psi_states:
                successors = forward_index.get(str(s), set())
                if s in phi_states or not successors or successors.issubset(result):
                    new_result.add(s)

        if new_result == result:
            break
        result = new_result

    return result


def pre_image_exist_with_trace(
    transitions: list[tuple[Any, Any]],
    target_states: set[str],
) -> tuple[set[str], dict[str, str]]:
    """Existential pre-image plus a predecessor-to-successor map for trace building."""
    target_states = {str(s) for s in target_states}
    reverse_index = _build_reverse_index(transitions)
    predecessors = set()
    predecessors_map: dict[str, str] = {}
    for state in target_states:
        state_str = str(state)
        if state_str in reverse_index:
            for pred in reverse_index[state_str]:
                predecessors.add(pred)
                if pred not in predecessors_map:
                    predecessors_map[pred] = state_str
    return predecessors, predecessors_map
