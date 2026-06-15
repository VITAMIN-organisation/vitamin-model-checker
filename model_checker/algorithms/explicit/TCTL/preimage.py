"""TCTL pre-images."""

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    discrete_pre_image_states,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS


def pre_image_exist(tcgs: TimedCGS, target_states, constraints: tuple | str | None):
    """Backward step with optional clock guards (DBM)."""
    if not constraints:
        return discrete_pre_image_states(tcgs, target_states)

    pre_list = set()
    targets = {str(state) for state in target_states}
    for source, target in tcgs.get_edges():
        if target not in targets:
            continue
        zone_predecessors = DBMAdapter.compute_predecessors(
            tcgs, source, target, constraints
        )
        if any(not zone.is_empty() for zone in zone_predecessors):
            pre_list.add(source)
    return pre_list
