"""Helpers shared by TCTL and TOL."""

from typing import TYPE_CHECKING

from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.error_handler import undeclared_propositions_message

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS


def states_where_prop_holds(tcgs: "TimedCGS", prop: str) -> set[int]:
    """State indices where prop holds; an undeclared prop is a semantic error, not false everywhere."""
    index = proposition_index(tcgs.atomic_propositions, prop)
    if index is None:
        raise ValueError(
            "[SEMANTIC] "
            + undeclared_propositions_message({prop}, tcgs.atomic_propositions)
        )
    return {
        state_idx
        for state_idx, row in enumerate(tcgs.matrix_prop)
        if row[int(index)] == 1
    }
