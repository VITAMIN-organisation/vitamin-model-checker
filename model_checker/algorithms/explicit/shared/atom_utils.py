"""
Shared atom resolution utilities for model checking algorithms.

This module provides common atom-related operations used across multiple
logic implementations (ATL, CTL, LTL, NatATL, etc.) to avoid code duplication.

Key Design Decisions:
- resolve_atom() converts atomic propositions to state sets where they hold
- Uses engine.runner.states_where_prop_holds for consistent behavior
- Returns a normalized set of state names for tree node values.
"""

from typing import Any, Optional, Protocol, Set, runtime_checkable

from model_checker.algorithms.explicit.shared.state_utils import (
    normalize_state_set,
)
from model_checker.engine.runner import states_where_prop_holds


@runtime_checkable
class AtomicModel(Protocol):
    """Protocol for models that support atomic proposition resolution."""

    # Minimal surface needed by states_where_prop_holds; kept broad to avoid tight coupling.
    atomic_propositions: Any

    def get_atom_index(self, element: str) -> Optional[int]: ...


def resolve_atom(cgs: AtomicModel, atom: str) -> Optional[Set[str]]:
    """
    Resolve atomic proposition into the set of state names where it holds.

    Args:
        cgs: Model parser instance (CGS, costCGS, or capCGS)
        atom: Atomic proposition name (e.g., 'p', 'q', 'goal')

    Returns:
        Set of state names where atom holds, or None if the atom doesn't exist.
    """
    states = states_where_prop_holds(cgs, str(atom))
    if states is None:
        return None
    return normalize_state_set(states)


def resolve_atom_with_constants(
    cgs: AtomicModel, atom: str, parser: Any
) -> Optional[Set[str]]:
    """
    Resolve atom including TRUE/FALSE constants using the logic's parser.

    Args:
        cgs: Model parser instance.
        atom: Atomic proposition or constant.
        parser: Formula parser instance with verify() method.
    """
    s = str(atom)
    if parser.verify("FALSE", s):
        return set()
    if parser.verify("TRUE", s):
        all_states = cgs.all_states_set
        return set(all_states) if not isinstance(all_states, set) else all_states

    return resolve_atom(cgs, s)
