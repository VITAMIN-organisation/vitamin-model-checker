"""TOL cost-bounded pre-image on region-graph regions."""

from model_checker.parsers.game_structures.timed_cgs.regions import (
    RegionSet,
    timed_predecessors,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import (
    TimeState,
    ZoneGraph,
)


def _transition_cost(tcgs: TimedCGS, source_idx: int, target_idx: int) -> int:
    value = tcgs.graph[source_idx][target_idx]
    if value in (0, "0", "*"):
        return 0
    if isinstance(value, str) and ":" in value:
        return sum(int(part) for part in value.split(":") if part.isdigit())
    return int(value)


def _demon_keeps_inside(
    tcgs: TimedCGS,
    zone_graph: ZoneGraph,
    region: TimeState,
    bound: int,
    inside: RegionSet,
) -> bool:
    """True when the Demon, within ``bound``, can disable every edge from ``region``
    that may leave ``inside``; a delay of 0 keeps every region a step to itself."""
    delay_targets = zone_graph.delay_successors[region] | {region}
    if not delay_targets <= inside:
        return False  # time passing cannot be disabled
    edges = zone_graph.discrete_successors[region]
    leaving = {
        target for target, successors in edges.items() if not successors <= inside
    }
    if leaving.issuperset(zone_graph.location_targets[region.location]):
        return False  # the Demon may not disable every edge of the location
    source_idx = tcgs.get_index_by_state_name(region.location)
    exit_cost = sum(
        _transition_cost(tcgs, source_idx, tcgs.get_index_by_state_name(target))
        for target in leaving
    )
    return exit_cost <= bound


def triangle_down(
    tcgs: TimedCGS, zone_graph: ZoneGraph, bound: int, regions: RegionSet
) -> RegionSet:
    """Regions from which the Demon, within ``bound``, can force the next step into
    ``regions``."""
    return {
        region
        for region in timed_predecessors(zone_graph, regions) | regions
        if _demon_keeps_inside(tcgs, zone_graph, region, bound, regions)
    }
