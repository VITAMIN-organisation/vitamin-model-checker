"""TOL formula evaluation."""

from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    eval_atomic_prop,
    eval_simple_time_expr,
    handle_and,
    handle_clock_expr,
    handle_implies,
    handle_not,
    handle_or,
    solve_ast_children,
)
from model_checker.algorithms.explicit.TOL.operators import (
    handle_eventually,
    handle_globally,
    handle_next,
    handle_release,
    handle_until,
    handle_weak,
)
from model_checker.parsers.formulas.TOL.tol_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    SimpleTimeExpr,
    Unary,
    verify,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def solve_tree(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: Expr) -> None:
    """Bottom-up AST evaluation."""
    if isinstance(node, AtomicProp):
        eval_atomic_prop(tcgs, node)
        return

    if isinstance(node, SimpleTimeExpr):
        eval_simple_time_expr(tcgs, zone_graph, node)
        return

    solve_ast_children(tcgs, zone_graph, node, solve_tree)

    if isinstance(node, Unary) and verify("NOT", node.op):
        handle_not(tcgs, node)
    elif isinstance(node, Binary):
        if verify("OR", node.op):
            handle_or(node)
        elif verify("AND", node.op):
            handle_and(node)
        elif verify("IMPLIES", node.op):
            handle_implies(tcgs, node)
    elif isinstance(node, DemonicOp):
        if verify("GLOBALLY", node.op):
            handle_globally(tcgs, zone_graph, node)
        elif verify("NEXT", node.op):
            handle_next(tcgs, zone_graph, node)
        elif verify("EVENTUALLY", node.op):
            handle_eventually(tcgs, zone_graph, node)
    elif isinstance(node, DemonicBinary):
        if verify("UNTIL", node.op):
            handle_until(tcgs, zone_graph, node)
        elif verify("RELEASE", node.op):
            handle_release(tcgs, zone_graph, node)
        elif verify("WEAK", node.op):
            handle_weak(tcgs, zone_graph, node)
    elif isinstance(node, ClockExpr):
        handle_clock_expr(node)
