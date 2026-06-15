"""Boolean and leaf operators for TCTL/TOL AST nodes (satisfying_states sets)."""

from typing import TYPE_CHECKING, Callable

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
    node.satisfying_states = all_states - node.operand.satisfying_states


def handle_or(node) -> None:
    node.satisfying_states = node.left.satisfying_states.union(
        node.right.satisfying_states
    )


def handle_and(node) -> None:
    node.satisfying_states = node.left.satisfying_states.intersection(
        node.right.satisfying_states
    )


def handle_implies(tcgs: "TimedCGS", node) -> None:
    all_states = set(tcgs.states)
    not_left = all_states - node.left.satisfying_states
    node.satisfying_states = not_left.union(node.right.satisfying_states)


def handle_clock_expr(node) -> None:
    node.satisfying_states = node.subject.satisfying_states
