"""TCTL formula evaluation (region-level rsat)."""

from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    eval_atomic_prop,
    eval_boolean_const,
    eval_simple_time_expr,
    handle_and,
    handle_clock_expr,
    handle_freeze,
    handle_implies,
    handle_not,
    handle_or,
    solve_ast_children,
)
from model_checker.algorithms.explicit.TCTL.operators import (
    handle_af,
    handle_ag,
    handle_au,
    handle_ef,
    handle_eg,
    handle_eu,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.TCTL import QuantifiedPath
from model_checker.parsers.formulas.timed_ast import (
    AtomicProp,
    Binary,
    BooleanConst,
    ClockExpr,
    Expr,
    FreezeExpr,
    SimpleTimeExpr,
    Unary,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def solve_tree(
    tcgs: "TimedCGS",
    zone_graph: "ZoneGraph",
    node: Expr,
    parser=None,
) -> None:
    """Bottom-up regional satisfiability (rsat)."""
    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("TCTL")

    if isinstance(node, AtomicProp):
        eval_atomic_prop(tcgs, zone_graph, node)
        return

    if isinstance(node, BooleanConst):
        eval_boolean_const(zone_graph, node)
        return

    if isinstance(node, SimpleTimeExpr):
        eval_simple_time_expr(tcgs, zone_graph, node)
        return

    def _recurse(t, z, n):
        solve_tree(t, z, n, parser)

    solve_ast_children(tcgs, zone_graph, node, _recurse)

    if isinstance(node, Unary):
        handle_not(zone_graph, node)
    elif isinstance(node, ClockExpr):
        handle_clock_expr(tcgs, zone_graph, node)
    elif isinstance(node, FreezeExpr):
        handle_freeze(zone_graph, node)
    elif isinstance(node, Binary):
        if parser.verify("OR", node.op):
            handle_or(node)
        elif parser.verify("AND", node.op):
            handle_and(node)
        elif parser.verify("IMPLIES", node.op):
            handle_implies(zone_graph, node)
    elif isinstance(node, QuantifiedPath):
        if parser.verify("EXIST", node.quantifier) and parser.verify(
            "EVENTUALLY", node.quantifier
        ):
            handle_ef(zone_graph, node)
        elif parser.verify("FORALL", node.quantifier) and parser.verify(
            "EVENTUALLY", node.quantifier
        ):
            handle_af(zone_graph, node)
        elif parser.verify("EXIST", node.quantifier) and parser.verify(
            "GLOBALLY", node.quantifier
        ):
            handle_eg(zone_graph, node)
        elif parser.verify("FORALL", node.quantifier) and parser.verify(
            "GLOBALLY", node.quantifier
        ):
            handle_ag(zone_graph, node)
        elif parser.verify("EXIST", node.quantifier) and parser.verify(
            "UNTIL", node.formula.op
        ):
            handle_eu(zone_graph, node)
        elif parser.verify("FORALL", node.quantifier) and parser.verify(
            "UNTIL", node.formula.op
        ):
            handle_au(zone_graph, node)
