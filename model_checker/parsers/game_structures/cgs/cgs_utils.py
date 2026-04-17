"""Helpers for CGS: state/index lookups, graph edges, action lists, keys."""

from typing import Dict, List, Optional, Set, Tuple

import numpy as np


def get_index_by_state_name(states, state: str) -> int:
    """Return the index of the state with the given name. Raises IndexError if not found."""
    return np.where(states == state)[0][0]


def get_state_name_by_index(states, index: int) -> str:
    """Return the state name at the given index. Raises IndexError if index is negative or out of range."""
    if index < 0:
        raise IndexError(f"State index must be non-negative, got {index}")
    if index >= len(states):
        raise IndexError(
            f"State index {index} is out of bounds for {len(states)} states"
        )
    return states[index]


def get_atom_index(atomic_propositions, element: str) -> Optional[int]:
    """Return the index of the given atomic proposition, or None if it is not in the list."""
    try:
        return np.where(atomic_propositions == element)[0][0]
    except IndexError:
        return None


def get_edges(graph: List[List], states) -> List[Tuple[str, str]]:
    """Build the list of (source_state, target_state) edges from the transition matrix."""
    return [
        (states[i], states[i] if element == "*" else states[j])
        for i, row in enumerate(graph)
        for j, element in enumerate(row)
        if element == "*" or element != 0
    ]


def build_reverse_index(
    edges: List[Tuple[str, str]],
) -> Dict[str, Set[str]]:
    """Build target -> set of sources from a list of (source, target) edges."""
    reverse_index: Dict[str, Set[str]] = {}
    for source, target in edges:
        target_str = str(target)
        if target_str not in reverse_index:
            reverse_index[target_str] = set()
        reverse_index[target_str].add(str(source))
    return reverse_index


def build_action_list(action_string: str, num_agents: int) -> List[str]:
    """Turn an action string into a list: "*" is expanded to num_agents chars, then split on commas."""
    if action_string == "*":
        action_string = "*" * num_agents
    action_list = action_string.split(",")
    return action_list


def translate_action_and_state_to_key(action_string: str, state: str) -> str:
    """Combine action string and state name into a single key (action;state)."""
    return action_string + ";" + state
