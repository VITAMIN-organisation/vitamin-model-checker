"""TCTL region labelling (rsat) on the zone graph."""

from typing import TYPE_CHECKING, Callable

from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    collect_formula_clocks,
)
from model_checker.parsers.game_structures.timed_cgs.regions import (
    RegionSet,
    all_regions,
    region_matches_label,
    region_with_clock_reset,
    regions_at_location,
    regions_where_prop_holds,
    regions_with_clock_guard,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

AST_CHILD_ATTRS = ("operand", "left", "right", "formula", "subject")


def solve_ast_children(
    tcgs: "TimedCGS",
    zone_graph: "ZoneGraph",
    node,
    solve_tree_fn: Callable,
) -> None:
    for attr_name in AST_CHILD_ATTRS:
        child = getattr(node, attr_name, None)
        if child is not None:
            solve_tree_fn(tcgs, zone_graph, child)


def eval_atomic_prop(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    node.satisfying_regions = regions_where_prop_holds(tcgs, zone_graph, node.name)


def eval_simple_time_expr(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    node.satisfying_regions = regions_with_clock_guard(
        tcgs, zone_graph, node.constraints
    )


def handle_not(zone_graph: "ZoneGraph", node) -> None:
    universe = all_regions(zone_graph)
    node.satisfying_regions = universe - node.operand.satisfying_regions


def handle_or(node) -> None:
    node.satisfying_regions = (
        node.left.satisfying_regions | node.right.satisfying_regions
    )


def handle_and(node) -> None:
    node.satisfying_regions = (
        node.left.satisfying_regions & node.right.satisfying_regions
    )


def handle_implies(zone_graph: "ZoneGraph", node) -> None:
    universe = all_regions(zone_graph)
    node.satisfying_regions = (
        universe - node.left.satisfying_regions
    ) | node.right.satisfying_regions


def handle_clock_expr(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    guard_regions = regions_with_clock_guard(tcgs, zone_graph, node.constraints)
    node.satisfying_regions = node.subject.satisfying_regions & guard_regions


def handle_freeze(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    """y.reset(phi): evaluate phi with formula clock y reset to 0."""
    operand_clocks = set(collect_formula_clocks(node.operand, set(tcgs.clocks)))
    if node.clock not in operand_clocks:
        node.satisfying_regions = set(node.operand.satisfying_regions)
        return

    operand_regions = node.operand.satisfying_regions
    node.satisfying_regions = {
        region
        for region in all_regions(zone_graph)
        if region_matches_label(
            region_with_clock_reset(tcgs, region, node.clock),
            operand_regions,
        )
    }


def initial_location_satisfied(
    zone_graph: "ZoneGraph", location: str, regions: RegionSet
) -> bool:
    return bool(regions_at_location(zone_graph, location) & regions)
