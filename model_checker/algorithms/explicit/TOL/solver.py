"""TOL formula evaluation."""

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
from model_checker.algorithms.explicit.TOL.operators import (
    handle_eventually,
    handle_globally,
    handle_release,
    handle_until,
    handle_weak,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
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
from model_checker.parsers.formulas.TOL.parser import DemonicBinary, DemonicOp

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def solve_tree(
    tcgs: "TimedCGS",
    zone_graph: "ZoneGraph",
    node: Expr,
    parser=None,
) -> None:
    """Bottom-up AST evaluation."""
    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("TOL")

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

    if isinstance(node, Unary) and parser.verify("NOT", node.op):
        handle_not(zone_graph, node)
    elif isinstance(node, Binary):
        if parser.verify("OR", node.op):
            handle_or(node)
        elif parser.verify("AND", node.op):
            handle_and(node)
        elif parser.verify("IMPLIES", node.op):
            handle_implies(zone_graph, node)
    elif isinstance(node, DemonicOp):
        if parser.verify("GLOBALLY", node.op):
            handle_globally(tcgs, zone_graph, node)
        elif parser.verify("EVENTUALLY", node.op):
            handle_eventually(tcgs, zone_graph, node)
    elif isinstance(node, DemonicBinary):
        if parser.verify("UNTIL", node.op):
            handle_until(tcgs, zone_graph, node)
        elif parser.verify("RELEASE", node.op):
            handle_release(tcgs, zone_graph, node)
        elif parser.verify("WEAK", node.op):
            handle_weak(tcgs, zone_graph, node)
    elif isinstance(node, ClockExpr):
        handle_clock_expr(tcgs, zone_graph, node)
    elif isinstance(node, FreezeExpr):
        handle_freeze(zone_graph, node)
