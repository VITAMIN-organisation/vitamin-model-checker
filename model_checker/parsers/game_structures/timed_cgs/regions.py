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


def region_matches_label(region: TimeState, label: RegionSet) -> bool:
    """Whether a labelled zone at the same location contains ``region``, so a zone
    changed by a clock reset still counts as satisfying the formula."""
    for other in label:
        if other.location != region.location:
            continue
        if other.zone == region.zone or region.zone.includes(other.zone):
            return True
    return False


def region_with_clock_reset(
    tcgs: "TimedCGS", region: TimeState, clock_name: str
) -> TimeState:
    """Copy of ``region`` with the named clock reset to zero."""
    clock_index = tcgs.clocks_dict[clock_name] + 1
    zone = region.zone.copy()
    zone.reset(clock_index, 0)
    return TimeState(region.location, zone)


def timed_predecessors(zone_graph: "ZoneGraph", targets: RegionSet) -> RegionSet:
    """Symbolic states that reach ``targets`` in one delay or discrete step."""
    predecessors: RegionSet = set()
    for target in targets:
        predecessors.update(zone_graph.reverse_graph.get(target, []))
    return predecessors
