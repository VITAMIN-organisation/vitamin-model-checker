"""State set helpers used by several model checkers."""

from typing import Any, Iterable, Set

from model_checker.parsers.game_structures.cgs import CGSProtocol


def state_names_to_indices(cgs: CGSProtocol, state_names: Iterable[Any]) -> Set[int]:
    """Map state names to their indices; unknown names are skipped."""
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
    """Map state indices to names; invalid indices are skipped."""
    names = set()
    for idx in state_indices:
        try:
            name = cgs.get_state_name_by_index(int(idx))
            if name is not None:
                names.add(str(name))
        except (ValueError, IndexError, AttributeError):
            pass
    return names
