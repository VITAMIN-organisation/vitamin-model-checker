"""TCTL temporal operators (region-level rsat) over time-divergent paths."""

from functools import lru_cache
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.parsers.formulas.TCTL import QuantifiedPath
from model_checker.parsers.formulas.timed_ast import Binary
from model_checker.parsers.game_structures.timed_cgs.regions import (
    RegionSet,
    all_regions,
    timed_predecessors,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def _until(zone_graph: "ZoneGraph", phi: RegionSet, target: RegionSet) -> RegionSet:
    """Regions with a path through ``phi`` into ``target``."""
    return least_fixpoint(
        target,
        lambda regions: target | (phi & timed_predecessors(zone_graph, regions)),
    )


def _divergent_globally(zone_graph: "ZoneGraph", phi: RegionSet) -> RegionSet:
    """Regions with a time-divergent path that stays in ``phi``: one that passes a
    tick region infinitely often."""
    ticks = zone_graph.tick_states
    return greatest_fixpoint(
        all_regions(zone_graph),
        lambda regions: phi
        & timed_predecessors(zone_graph, _until(zone_graph, phi, regions & ticks)),
    )


@lru_cache(maxsize=1)
def _timelock_free(zone_graph: "ZoneGraph") -> frozenset:
    """Regions with some time-divergent path; one formula asks for it many times."""
    return frozenset(_divergent_globally(zone_graph, all_regions(zone_graph)))


def _divergent_until(
    zone_graph: "ZoneGraph", phi: RegionSet, psi: RegionSet
) -> RegionSet:
    """E(phi U psi), with a time-divergent path going on from psi."""
    return _until(zone_graph, phi, psi & _timelock_free(zone_graph))


def _until_operands(node: QuantifiedPath) -> tuple[RegionSet, RegionSet]:
    until = node.formula
    if not isinstance(until, Binary):
        raise TypeError(f"Expected an until formula under {node!r}, got {until!r}")
    return until.left.satisfying_regions, until.right.satisfying_regions


def handle_ef(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    node.satisfying_regions = _divergent_until(
        zone_graph, all_regions(zone_graph), node.formula.satisfying_regions
    )


def handle_eg(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    node.satisfying_regions = _divergent_globally(
        zone_graph, node.formula.satisfying_regions
    )


def handle_eu(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    node.satisfying_regions = _divergent_until(zone_graph, *_until_operands(node))


def handle_af(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    not_phi = universe - node.formula.satisfying_regions
    node.satisfying_regions = universe - _divergent_globally(zone_graph, not_phi)


def handle_ag(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    not_phi = universe - node.formula.satisfying_regions
    node.satisfying_regions = universe - _divergent_until(zone_graph, universe, not_phi)


def handle_au(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    # A(phi U psi) = !(E(!psi U (!phi & !psi)) | EG !psi)
    universe = all_regions(zone_graph)
    phi, psi = _until_operands(node)
    not_phi = universe - phi
    not_psi = universe - psi
    node.satisfying_regions = universe - (
        _divergent_until(zone_graph, not_psi, not_phi & not_psi)
        | _divergent_globally(zone_graph, not_psi)
    )
