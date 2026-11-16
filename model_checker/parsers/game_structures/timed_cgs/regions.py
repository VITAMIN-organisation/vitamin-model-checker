"""Helpers that lift discrete location facts onto region-graph regions for TCTL."""

from typing import TYPE_CHECKING

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    states_where_prop_holds,
)
from model_checker.parsers.game_structures.timed_cgs.zone_graph import TimeState

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

RegionSet = set[TimeState]


def all_regions(zone_graph: "ZoneGraph") -> RegionSet:
    return set(zone_graph.states)


def project_regions_to_locations(regions: RegionSet) -> set[str]:
    return {state.location for state in regions}


def regions_where_prop_holds(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", prop: str
) -> RegionSet:
    prop_indices = states_where_prop_holds(tcgs, prop)
    location_names = {
        str(tcgs.get_state_name_by_index(index)) for index in prop_indices
    }
    return {state for state in zone_graph.states if state.location in location_names}


def regions_with_clock_guard(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", guard: str | tuple
) -> RegionSet:
    if isinstance(guard, tuple):
        guard_text = "".join(guard)
    else:
        guard_text = str(guard)
    guards, resets = DBMAdapter.parse_constraints([guard_text], tcgs.clocks_dict)
    return {
        state
        for state in zone_graph.states
        if DBMAdapter.zone_satisfies_guards(
            tcgs, state.location, state.zone, guards, resets
        )
    }


def timed_predecessors(zone_graph: "ZoneGraph", targets: RegionSet) -> RegionSet:
    """Symbolic states that reach ``targets`` in one delay or discrete step."""
    predecessors: RegionSet = set()
    for target in targets:
        predecessors.update(zone_graph.reverse_graph.get(target, []))
    return predecessors
