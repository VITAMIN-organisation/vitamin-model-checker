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

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def handle_ef(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    target = node.formula.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        target,
        lambda regions: regions | timed_predecessors(zone_graph, regions),
    )


def handle_af(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    # AF phi = !EG(!phi) = universe \ gfp Z. (!phi & Pre(Z))
    universe = all_regions(zone_graph)
    not_phi = universe - node.formula.satisfying_regions
    node.satisfying_regions = universe - greatest_fixpoint(
        universe,
        lambda regions: not_phi & timed_predecessors(zone_graph, regions),
    )


def handle_eg(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    target = node.formula.satisfying_regions
    node.satisfying_regions = greatest_fixpoint(
        universe,
        lambda regions: target & timed_predecessors(zone_graph, regions),
    )


def handle_ag(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    universe = all_regions(zone_graph)
    target = universe - node.formula.satisfying_regions
    unreachable = least_fixpoint(
        target,
        lambda regions: regions | timed_predecessors(zone_graph, regions),
    )
    node.satisfying_regions = universe - unreachable


def handle_eu(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    sat_phi = node.formula.left.satisfying_regions
    sat_psi = node.formula.right.satisfying_regions
    node.satisfying_regions = least_fixpoint(
        sat_psi,
        lambda regions: (sat_psi | (sat_phi & timed_predecessors(zone_graph, regions))),
    )


def handle_au(zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    # A[phi U psi] = universe \ lfp Z. !psi | (!phi & !psi & AX(Z))
    # AX(Z) = universe \ Pre_exists(universe \ Z)  (universal backward step)
    universe = all_regions(zone_graph)
    sat_phi = node.formula.left.satisfying_regions
    sat_psi = node.formula.right.satisfying_regions
    not_phi = universe - sat_phi
    not_psi = universe - sat_psi
    unreachable = least_fixpoint(
        not_psi,
        lambda regions: (
            not_psi
            | (
                not_phi
                & not_psi
                & (universe - timed_predecessors(zone_graph, universe - regions))
            )
        ),
    )
    node.satisfying_regions = universe - unreachable
