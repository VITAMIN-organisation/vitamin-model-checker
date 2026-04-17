"""Pre-image computation for CTL (EX, AX, Release) and predecessor tracking for traces."""

from typing import Any, Dict, List, Optional, Set, Tuple

from model_checker.algorithms.explicit.shared import normalize_state_set
from model_checker.parsers.game_structures.cgs import CGSProtocol


def _build_reverse_index(
    transitions: List[Tuple[Any, Any]],
) -> Dict[str, Set[str]]:
    """Build reverse index: target -> set of source states."""
    reverse_index: Dict[str, Set[str]] = {}
    for source, target in transitions:
        target_str = str(target)
        if target_str not in reverse_index:
            reverse_index[target_str] = set()
        reverse_index[target_str].add(str(source))
    return reverse_index


def pre_image_exist(
    transitions: List[Tuple[Any, Any]],
    target_states: Set[str],
    reverse_index: Optional[Dict[str, Set[str]]] = None,
) -> Set[str]:
    """Existential pre-image (EX): states with at least one successor in target_states.

    Args:
        transitions: List of (source, target) pairs.
        target_states: Target state names.
        reverse_index: Optional pre-built reverse index.

    Returns:
        Set of predecessor state names.
    """
    target_states = normalize_state_set(target_states)

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
    transitions: List[Tuple[Any, Any]],
    all_states: Set[str],
    target_states: Set[str],
) -> Set[str]:
    """Universal pre-image (AX): states whose successors are all in target_states.

    States with no successors are included (vacuous case).

    Args:
        transitions: List of (source, target) pairs.
        all_states: All state names in the model.
        target_states: Target state names.

    Returns:
        Set of state names satisfying AX predecessor condition.
    """
    all_states = normalize_state_set(all_states)
    target_states = normalize_state_set(target_states)

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
    phi_states: Set[str],
    psi_states: Set[str],
) -> Set[str]:
    """Compute A(phi R psi) via greatest fixpoint (psi and (phi or AX Z)).

    Args:
        cgs: CGS model.
        phi_states: States where phi holds.
        psi_states: States where psi holds.

    Returns:
        Set of states satisfying A(phi R psi).
    """
    all_states = cgs.all_states_set
    phi_states = normalize_state_set(phi_states)
    psi_states = normalize_state_set(psi_states)

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
    transitions: List[Tuple[Any, Any]],
    target_states: Set[str],
) -> Tuple[Set[str], Dict[str, str]]:
    """Existential pre-image plus a predecessor -> successor map for trace building.

    Args:
        transitions: List of (source, target) pairs.
        target_states: Target state names.

    Returns:
        (predecessor_states, predecessors_map) with one chosen successor per predecessor.
    """
    target_states = normalize_state_set(target_states)
    reverse_index = _build_reverse_index(transitions)
    predecessors = set()
    predecessors_map: Dict[str, str] = {}
    for state in target_states:
        state_str = str(state)
        if state_str in reverse_index:
            for pred in reverse_index[state_str]:
                predecessors.add(pred)
                if pred not in predecessors_map:
                    predecessors_map[pred] = state_str
    return predecessors, predecessors_map
