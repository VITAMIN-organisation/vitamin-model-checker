"""TOL cost-bounded pre-images."""

from model_checker.parsers.game_structures.timed_cgs.semantics import (
    discrete_pre_image_states,
    zone_graph_pre_image_states,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def _transition_cost(tcgs: TimedCGS, source_idx: int, target_idx: int) -> int:
    value = tcgs.graph[source_idx][target_idx]
    if value in (0, "0", "*"):
        return 0
    if isinstance(value, str) and ":" in value:
        return sum(int(part) for part in value.split(":") if part.isdigit())
    return int(value)


def pre_indices(tcgs: TimedCGS, state_indices: set[int]) -> set[int]:
    target_names = {str(tcgs.get_state_name_by_index(idx)) for idx in state_indices}
    pre_names = discrete_pre_image_states(tcgs, target_names)
    return {int(tcgs.get_index_by_state_name(name)) for name in pre_names}


def pre_timed_indices(
    tcgs: TimedCGS,
    zone_graph: ZoneGraph,
    state_indices: set[int],
    constraints,
) -> set[int]:
    target_names = {str(tcgs.get_state_name_by_index(idx)) for idx in state_indices}
    pre_names = zone_graph_pre_image_states(tcgs, zone_graph, target_names, constraints)
    return {int(tcgs.get_index_by_state_name(name)) for name in pre_names}


def triangle(tcgs: TimedCGS, source_idx: int, bound: int, excluded: set[int]) -> bool:
    total = 0
    for target_idx, _ in enumerate(tcgs.graph[source_idx]):
        if target_idx in excluded:
            continue
        total += _transition_cost(tcgs, source_idx, target_idx)
    return total <= bound


def triangle_down(
    tcgs: TimedCGS,
    zone_graph: ZoneGraph,
    bound: int,
    state_names,
    constraints=None,
) -> set[str]:
    state_indices = {int(tcgs.get_index_by_state_name(name)) for name in state_names}
    excluded = {idx for idx in range(len(tcgs.graph)) if idx not in state_indices}
    if constraints:
        predecessors = pre_timed_indices(tcgs, zone_graph, state_indices, constraints)
    else:
        predecessors = pre_indices(tcgs, state_indices)
    result = {idx for idx in predecessors if triangle(tcgs, idx, bound, excluded)}
    return {str(tcgs.get_state_name_by_index(idx)) for idx in result}
