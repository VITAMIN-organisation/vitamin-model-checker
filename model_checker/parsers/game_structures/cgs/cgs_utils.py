"""Helpers for CGS: proposition validation, graph edges, and action list parsing."""

import re
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from model_checker.parsers.syntax_patterns import ATOMIC_PROPOSITION_NAME_RE


def proposition_index(atomic_propositions, element) -> Optional[int]:
    """Return the index of element in atomic_propositions, or None if absent."""
    try:
        return int(np.where(atomic_propositions == element)[0][0])
    except (IndexError, TypeError):
        return None


def validate_atomic_proposition_name(name: str) -> None:
    """Reject proposition names that formula parsers cannot reference."""
    if not ATOMIC_PROPOSITION_NAME_RE.match(str(name)):
        raise ValueError(
            f"Atomic proposition {name!r} is invalid: expected identifier matching "
            "[a-zA-Z][a-zA-Z0-9_]*."
        )


AGENT_LABEL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_agent_label_name(name: str) -> None:
    """Reject agent display labels that cannot be stored in Agent_labels."""
    label = str(name).strip()
    if not label or not AGENT_LABEL_NAME_RE.match(label):
        raise ValueError(
            f"Agent label {name!r} is invalid: use non-empty tokens matching "
            "[a-zA-Z0-9_-]+ (whitespace-separated in Agent_labels)."
        )


def default_agent_labels(number_of_agents: int) -> List[str]:
    """Return canonical default labels '1', '2', ... for the given agent count."""
    if number_of_agents <= 0:
        return []
    return [str(i + 1) for i in range(number_of_agents)]


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
    return action_string.split(",")
