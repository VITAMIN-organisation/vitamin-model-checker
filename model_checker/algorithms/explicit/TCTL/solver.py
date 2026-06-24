"""TCTL formula evaluation (region-level rsat)."""

from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.TCTL.evaluators import (
    eval_atomic_prop,
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
from model_checker.parsers.formulas.TCTL import (
    AtomicProp,
    Binary,
    ClockExpr,
    Expr,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
    verifyTCTL,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def solve_tree(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: Expr) -> None:
    """Bottom-up regional satisfiability (rsat)."""
    if isinstance(node, AtomicProp):
        eval_atomic_prop(tcgs, zone_graph, node)
        return

    if isinstance(node, SimpleTimeExpr):
        eval_simple_time_expr(tcgs, zone_graph, node)
        return

    solve_ast_children(tcgs, zone_graph, node, solve_tree)

    if isinstance(node, Unary):
        handle_not(zone_graph, node)
    elif isinstance(node, ClockExpr):
        handle_clock_expr(tcgs, zone_graph, node)
    elif isinstance(node, FreezeExpr):
        handle_freeze(tcgs, zone_graph, node)
    elif isinstance(node, Binary):
        if verifyTCTL("OR", node.op):
            handle_or(node)
        elif verifyTCTL("AND", node.op):
            handle_and(node)
        elif verifyTCTL("IMPLIES", node.op):
            handle_implies(zone_graph, node)
    elif isinstance(node, QuantifiedPath):
        if verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "EVENTUALLY", node.quantifier
        ):
            handle_ef(tcgs, zone_graph, node)
        elif verifyTCTL("FORALL", node.quantifier) and verifyTCTL(
            "EVENTUALLY", node.quantifier
        ):
            handle_af(tcgs, zone_graph, node)
        elif verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "GLOBALLY", node.quantifier
        ):
            handle_eg(tcgs, zone_graph, node)
        elif verifyTCTL("FORALL", node.quantifier) and verifyTCTL(
            "GLOBALLY", node.quantifier
        ):
            handle_ag(tcgs, zone_graph, node)
        elif verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "UNTIL", node.formula.op
        ):
            handle_eu(tcgs, zone_graph, node)
        elif verifyTCTL("FORALL", node.quantifier) and verifyTCTL(
            "UNTIL", node.formula.op
        ):
            handle_au(tcgs, zone_graph, node)
