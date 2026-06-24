"""TCTL temporal operators (region-level rsat)."""

from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.parsers.formulas.TCTL import QuantifiedPath
from model_checker.parsers.game_structures.timed_cgs.regions import (
    all_regions,
    timed_predecessors,
)
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    extract_closest_constraint,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def handle_ef(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    guard = extract_closest_constraint(node.formula)
    target = node.formula.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        target,
        lambda regions: regions | timed_predecessors(zone_graph, tcgs, regions, guard),
    )


def handle_af(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    guard = extract_closest_constraint(node.formula)
    target = universe - node.formula.satisfying_regions
    unreachable = least_fixpoint(
        target,
        lambda regions: regions | timed_predecessors(zone_graph, tcgs, regions, guard),
    )
    node.satisfying_regions = universe - unreachable


def handle_eg(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    guard = extract_closest_constraint(node.formula)
    target = node.formula.satisfying_regions
    node.satisfying_regions = greatest_fixpoint(
        universe,
        lambda regions: target & timed_predecessors(zone_graph, tcgs, regions, guard),
    )


def handle_ag(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    guard = extract_closest_constraint(node.formula)
    target = universe - node.formula.satisfying_regions
    unreachable = least_fixpoint(
        target,
        lambda regions: regions | timed_predecessors(zone_graph, tcgs, regions, guard),
    )
    node.satisfying_regions = universe - unreachable


def handle_eu(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    guard = extract_closest_constraint(node.formula)
    sat_phi = node.formula.left.satisfying_regions
    sat_psi = node.formula.right.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        sat_psi,
        lambda regions: sat_psi
        | (sat_phi & timed_predecessors(zone_graph, tcgs, regions, guard)),
    )


def handle_au(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    guard = extract_closest_constraint(node.formula)
    sat_phi = node.formula.left.satisfying_regions
    sat_psi = node.formula.right.satisfying_regions
    not_phi = universe - sat_phi
    not_psi = universe - sat_psi
    unreachable = least_fixpoint(
        not_psi,
        lambda regions: not_psi
        | (not_phi & not_psi & timed_predecessors(zone_graph, tcgs, regions, guard)),
    )
    node.satisfying_regions = universe - unreachable
