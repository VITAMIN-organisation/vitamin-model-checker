"""Steps shared by the TCTL and TOL checkers: leaf, boolean and freeze operators on
sets of regions, and the result they report."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    ast_children,
    collect_formula_clocks,
    extend_timed_cgs_clocks,
    formula_clock_constants,
    formula_freeze_clocks,
)
from model_checker.parsers.game_structures.timed_cgs.regions import (
    RegionSet,
    all_regions,
    project_regions_to_locations,
    regions_where_prop_holds,
    regions_with_clock_guard,
)
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph
from model_checker.utils.error_handler import create_error_response

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS


def _region_graph_for_formula(
    tcgs: "TimedCGS", ast, track_divergence: bool
) -> ZoneGraph:
    """The region graph of ``tcgs`` with the clocks, constants and freezes of ``ast``;
    a freeze on a clock of the model is a semantic error."""
    model_clocks = set(tcgs.clocks_dict)
    freeze_clocks = formula_freeze_clocks(ast)
    frozen_model_clocks = sorted(model_clocks.intersection(freeze_clocks))
    if frozen_model_clocks:
        raise ValueError(
            f"[SEMANTIC] Freeze on the model clock '{frozen_model_clocks[0]}': a "
            f"freeze names a formula clock, not a clock of the model "
            f"({', '.join(sorted(model_clocks))})."
        )
    extend_timed_cgs_clocks(tcgs, collect_formula_clocks(ast, model_clocks))
    return ZoneGraph(
        tcgs,
        formula_clock_constants(ast, tcgs.clocks_dict),
        freeze_clocks,
        track_divergence,
    )


def solve_ast_children(
    tcgs: "TimedCGS",
    zone_graph: ZoneGraph,
    node,
    solve_tree_fn: Callable,
) -> None:
    for child in ast_children(node):
        solve_tree_fn(tcgs, zone_graph, child)


def eval_atomic_prop(tcgs: "TimedCGS", zone_graph: ZoneGraph, node) -> None:
    node.satisfying_regions = regions_where_prop_holds(tcgs, zone_graph, node.name)


def eval_simple_time_expr(tcgs: "TimedCGS", zone_graph: ZoneGraph, node) -> None:
    node.satisfying_regions = regions_with_clock_guard(
        tcgs, zone_graph, node.constraints
    )


def eval_boolean_const(zone_graph: ZoneGraph, node) -> None:
    if node.value:
        node.satisfying_regions = all_regions(zone_graph)
    else:
        node.satisfying_regions = set()


def handle_not(zone_graph: ZoneGraph, node) -> None:
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


def handle_implies(zone_graph: ZoneGraph, node) -> None:
    universe = all_regions(zone_graph)
    node.satisfying_regions = (
        universe - node.left.satisfying_regions
    ) | node.right.satisfying_regions


def handle_clock_expr(tcgs: "TimedCGS", zone_graph: ZoneGraph, node) -> None:
    guard_regions = regions_with_clock_guard(tcgs, zone_graph, node.constraints)
    node.satisfying_regions = node.subject.satisfying_regions & guard_regions


def handle_freeze(zone_graph: ZoneGraph, node) -> None:
    """Label the regions whose freeze-clock reset satisfies the operand."""
    operand_regions = node.operand.satisfying_regions
    node.satisfying_regions = {
        region
        for region, reset in zone_graph.freeze_resets[node.clock].items()
        if reset in operand_regions
    }


def _timed_checking_result(
    tcgs: "TimedCGS", zone_graph: ZoneGraph, regions: RegionSet
) -> dict[str, Any]:
    """The res and initial_state dict; ``res`` lists the locations of regions that
    time and edges reach from the initial region (all clocks 0)."""
    is_satisfied = zone_graph.initial_time_state in regions
    locations = project_regions_to_locations(regions & zone_graph.reachable_states)
    return format_model_checking_result(
        locations, str(tcgs.initial_state), is_satisfied
    )


def timed_model_checking(
    logic: str, solve_tree_fn: Callable, track_divergence: bool
) -> Callable:
    """The model_checking entry of TCTL or TOL: parse, build the region graph, run
    the logic's solver over the formula tree."""

    def core(tcgs, formula: str) -> dict[str, Any]:
        parser = FormulaParserFactory.get_parser_instance(logic)
        ast = parser.parse(formula.strip())
        if ast is None:
            err = parser.errors[0] if parser.errors else "Syntax error in formula"
            return create_error_response("syntax", err)
        zone_graph = _region_graph_for_formula(tcgs, ast, track_divergence)
        solve_tree_fn(tcgs, zone_graph, ast)
        return _timed_checking_result(tcgs, zone_graph, ast.satisfying_regions)

    return create_model_checking_entry(logic, core)
