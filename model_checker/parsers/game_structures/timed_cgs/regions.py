"""Region-level helpers for TCTL rsat on the zone graph."""

from typing import TYPE_CHECKING, Set

from model_checker.algorithms.explicit.shared.trace_utils import reverse_adjacency
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    states_where_prop_holds,
)
from model_checker.parsers.game_structures.timed_cgs.zone_graph import TimeState

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

RegionSet = Set[TimeState]


def all_regions(zone_graph: "ZoneGraph") -> RegionSet:
    return set(zone_graph.states)


def regions_at_location(zone_graph: "ZoneGraph", location: str) -> RegionSet:
    return {state for state in zone_graph.states if state.location == location}


def project_regions_to_locations(regions: RegionSet) -> Set[str]:
    return {state.location for state in regions}


def regions_where_prop_holds(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", prop: str
) -> RegionSet:
    prop_indices = states_where_prop_holds(tcgs, prop)
    if prop_indices is None:
        return set()
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
    """True when label covers region at the same location (zone inclusion)."""
    for other in label:
        if other.location != region.location:
            continue
        if other.zone == region.zone or other.zone.includes(region.zone):
            return True
    return False


def region_with_clock_reset(
    tcgs: "TimedCGS", region: TimeState, clock_name: str
) -> TimeState:
    clock_index = tcgs.clocks_dict[clock_name] + 1
    zone = region.zone.copy()
    zone.reset(clock_index, 0)
    return TimeState(region.location, zone)


def timed_predecessors(
    zone_graph: "ZoneGraph",
    tcgs: "TimedCGS",
    targets: RegionSet,
    guard: str | tuple | None = None,
) -> RegionSet:
    """Backward step in the zone graph (delay and discrete edges)."""
    if not targets:
        return set()

    reverse_graph = getattr(zone_graph, "reverse_graph", None)
    if reverse_graph is None:
        reverse_graph = reverse_adjacency(zone_graph.graph, zone_graph.states)
        zone_graph.reverse_graph = reverse_graph

    guards = resets = None
    if guard:
        guard_text = "".join(guard) if isinstance(guard, tuple) else str(guard)
        guards, resets = DBMAdapter.parse_constraints([guard_text], tcgs.clocks_dict)

    predecessors: RegionSet = set()
    for target in targets:
        for predecessor in reverse_graph.get(target, []):
            if guard and not DBMAdapter.zone_satisfies_guards(
                tcgs,
                predecessor.location,
                predecessor.zone,
                guards,
                resets,
            ):
                continue
            predecessors.add(predecessor)
    return predecessors
