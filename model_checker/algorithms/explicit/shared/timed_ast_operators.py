"""Boolean and leaf operators for TCTL/TOL AST nodes (satisfying_states sets)."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.boolean_semantics import (
    compute_boolean_result,
)
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    states_where_prop_holds,
    states_with_time_constraints,
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


def eval_atomic_prop(tcgs: "TimedCGS", node) -> None:
    prop_states = states_where_prop_holds(tcgs, node.name)
    if prop_states is None:
        return
    for state_idx in prop_states:
        node.satisfying_states.add(str(tcgs.get_state_name_by_index(state_idx)))


def eval_simple_time_expr(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    node.satisfying_states = states_with_time_constraints(
        tcgs, zone_graph, node.constraints
    )


def handle_not(tcgs: "TimedCGS", node) -> None:
    all_states = set(tcgs.states)
    node.satisfying_states = compute_boolean_result(
        "NOT", node.operand.satisfying_states, all_states=all_states
    )


def handle_or(node) -> None:
    node.satisfying_states = compute_boolean_result(
        "OR", node.left.satisfying_states, right_states=node.right.satisfying_states
    )


def handle_and(node) -> None:
    node.satisfying_states = compute_boolean_result(
        "AND", node.left.satisfying_states, right_states=node.right.satisfying_states
    )


def handle_implies(tcgs: "TimedCGS", node) -> None:
    all_states = set(tcgs.states)
    node.satisfying_states = compute_boolean_result(
        "IMPLIES",
        node.left.satisfying_states,
        right_states=node.right.satisfying_states,
        all_states=all_states,
    )


def handle_clock_expr(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    guard_states = states_with_time_constraints(tcgs, zone_graph, node.constraints)
    node.satisfying_states = node.subject.satisfying_states & guard_states


def handle_freeze(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node) -> None:
    """Locations that satisfy the freeze operand after resetting the freeze clock.

    TOL reports location names: a location is kept when some zone there, after
    the reset, is covered by the operand's satisfying set.
    """
    from model_checker.parsers.game_structures.timed_cgs.regions import (
        region_matches_label,
        region_with_clock_reset,
        regions_at_location,
    )

    operand_locations = set(node.operand.satisfying_states)
    if node.clock not in tcgs.clocks_dict:
        node.satisfying_states = set(operand_locations)
        return

    operand_regions = set()
    for location in operand_locations:
        operand_regions |= regions_at_location(zone_graph, location)

    result: set[str] = set()
    for region in zone_graph.states:
        reset_region = region_with_clock_reset(tcgs, region, node.clock)
        if region_matches_label(reset_region, operand_regions):
            result.add(region.location)
    node.satisfying_states = result
