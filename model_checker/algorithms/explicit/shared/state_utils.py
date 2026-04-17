"""
Shared state utilities for model checking algorithms.

This module provides common state-related operations used across multiple
logic implementations (ATL, CTL, LTL, NatATL, etc.) to avoid code duplication.

Key Design Decisions:
- normalize_state_set() ensures consistent string representation of states,
  handling both numpy.str_ and Python str types that may come from model parsers.
- All functions use Python's built-in set operations for O(1) membership testing.
"""

from typing import Any, Iterable, Set

from model_checker.parsers.game_structures.cgs import CGSProtocol


def value_for_cache_key(value: Any) -> str:
    """
    Produce a deterministic string for use in solver cache keys.

    When the value is a state set, returns a sorted tuple repr so that
    cache keys do not depend on set iteration order.
    """
    if isinstance(value, set):
        return str(tuple(sorted(value)))
    return str(value)


def state_set_to_str(state_set: Iterable[Any]) -> str:
    """
    Serialize a state set to a deterministic string for storage in formula tree nodes.

    binarytree.Node only accepts str/int/float; this format is parseable by
    parse_state_set_literal (tuple form) and avoids non-deterministic set repr.
    """
    return str(tuple(sorted(normalize_state_set(state_set))))


def normalize_state_set(state_set: Iterable[Any]) -> Set[str]:
    """
    Normalize a set of states to ensure all are Python strings.

    Args:
        state_set: Set or iterable of state names (may be numpy.str_ or str)

    Returns:
        Set of Python strings

    Example:
        >>> normalize_state_set({'s0', 's1'})
        {'s0', 's1'}
        >>> import numpy as np
        >>> normalize_state_set([np.str_('s0')])
        {'s0'}
    """
    return {str(s) for s in state_set}


def states_intersection(set1: Iterable[Any], set2: Iterable[Any]) -> Set[str]:
    """
    Compute intersection of two state sets with normalization.

    Args:
        set1: First set of states
        set2: Second set of states

    Returns:
        Intersection as normalized set of strings
    """
    return normalize_state_set(set1) & normalize_state_set(set2)


def states_union(set1: Iterable[Any], set2: Iterable[Any]) -> Set[str]:
    """
    Compute union of two state sets with normalization.

    Args:
        set1: First set of states
        set2: Second set of states

    Returns:
        Union as normalized set of strings
    """
    return normalize_state_set(set1) | normalize_state_set(set2)


def states_difference(set1: Iterable[Any], set2: Iterable[Any]) -> Set[str]:
    """
    Compute difference of two state sets with normalization.

    Args:
        set1: First set of states (minuend)
        set2: Second set of states (subtrahend)

    Returns:
        Difference as normalized set of strings
    """
    return normalize_state_set(set1) - normalize_state_set(set2)


def state_names_to_indices(cgs: CGSProtocol, state_names: Iterable[Any]) -> Set[int]:
    """
    Convert a set of state names to their corresponding indices in the CGS.

    Args:
        cgs: The CGS model parser instance
        state_names: Iterable of state names (may be numpy.str_ or str)

    Returns:
        Set of state indices (integers)
    """
    indices = set()
    for name in state_names:
        name_str = str(name)
        try:
            idx = cgs.get_index_by_state_name(name_str)
            if idx is not None:
                indices.add(int(idx))
        except (ValueError, KeyError, AttributeError, IndexError):
            pass
    return indices


def state_indices_to_names(cgs: CGSProtocol, state_indices: Iterable[int]) -> Set[str]:
    """
    Convert a set of state indices to their corresponding names in the CGS.

    Args:
        cgs: The CGS model parser instance
        state_indices: Iterable of state indices (integers)

    Returns:
        Set of state names (normalized Python strings)
    """
    names = set()
    for idx in state_indices:
        try:
            name = cgs.get_state_name_by_index(int(idx))
            if name is not None:
                names.add(str(name))
        except (ValueError, IndexError, AttributeError):
            pass
    return names
