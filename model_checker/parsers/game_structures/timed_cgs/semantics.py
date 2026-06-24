"""Helpers shared by TCTL and TOL."""

from typing import TYPE_CHECKING

from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter

if TYPE_CHECKING:
    from model_checker.parsers.formulas.TCTL.tctl_ply_parser import Expr
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def states_where_prop_holds(tcgs: "TimedCGS", prop: str) -> set[int] | None:
    """State indices where prop holds; None if the atom is missing."""
    index = proposition_index(tcgs.atomic_propositions, prop)
    if index is None:
        return None
    return {
        state_idx
        for state_idx, row in enumerate(tcgs.matrix_prop)
        if row[int(index)] == 1
    }


def discrete_pre_image_states(tcgs: "TimedCGS", target_states) -> set[str]:
    """States with an edge into target_states."""
    targets = {str(state) for state in target_states}
    return {source for source, target in tcgs.get_edges() if target in targets}


def zone_graph_pre_image_states(
    tcgs: "TimedCGS",
    zone_graph: "ZoneGraph",
    target_states,
    constraints: tuple | str | None,
) -> set[str]:
    """States with a timed edge into target_states under the clock guard."""
    if not constraints:
        return discrete_pre_image_states(tcgs, target_states)
    target_names = {str(state) for state in target_states}
    clock_constraints, _ = DBMAdapter.parse_constraints([constraints], tcgs.clocks_dict)
    result: set[str] = set()
    for source, target in tcgs.get_edges():
        if target not in target_names:
            continue
        if zone_graph.has_path_from(target, clock_constraints):
            result.add(source)
    return result


def extract_closest_constraint(node: "Expr") -> str | None:
    """Nearest clock guard on this node or a descendant."""
    constraints = getattr(node, "constraints", None)
    if constraints:
        return constraints

    for attr_name in ("operand", "left", "right", "formula", "subject"):
        child = getattr(node, attr_name, None)
        if child is not None:
            found = extract_closest_constraint(child)
            if found:
                return found

    return None


def states_with_time_constraints(
    tcgs: "TimedCGS",
    zone_graph: "ZoneGraph",
    constraints: tuple[str, ...] | str,
) -> set[str]:
    """States whose zone satisfies the clock guard."""
    result: set[str] = set()
    guards, resets = DBMAdapter.parse_constraints([constraints], tcgs.clocks_dict)
    for state in sorted(zone_graph.states, key=lambda item: item.location):
        if DBMAdapter.zone_satisfies_guards(
            tcgs, state.location, state.zone, guards, resets
        ):
            result.add(state.location)
    return result
