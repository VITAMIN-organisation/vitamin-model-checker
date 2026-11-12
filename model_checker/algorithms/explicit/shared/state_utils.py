"""State set helpers used by several model checkers."""

from collections.abc import Iterable
from typing import Any

from model_checker.parsers.game_structures.cgs import CGSProtocol


def state_names_to_indices(cgs: CGSProtocol, state_names: Iterable[Any]) -> set[int]:
    """Map state names to their indices; an unknown name raises IndexError."""
    return {int(cgs.get_index_by_state_name(str(name))) for name in state_names}


def state_indices_to_names(cgs: CGSProtocol, state_indices: Iterable[int]) -> set[str]:
    """Map state indices to names; an index outside the model raises IndexError."""
    return {cgs.get_state_name_by_index(int(idx)) for idx in state_indices}
