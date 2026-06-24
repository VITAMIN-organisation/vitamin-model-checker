"""Formula clocks J for TOL (disjoint from automaton clocks X)."""

import re

from model_checker.parsers.formulas.TOL.tol_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    FreezeExpr,
    SimpleTimeExpr,
    Unary,
)

_CLOCK_BOUND_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_]*)(?:<=|>=|<|>)")


def _clock_from_constraint(text: str) -> str | None:
    match = _CLOCK_BOUND_RE.match(str(text))
    return match.group(1) if match else None


def collect_formula_clocks(node: Expr | None, model_clocks: set[str]) -> tuple[str, ...]:
    """Collect formula clock names from the AST that are not automaton clocks."""
    if node is None:
        return ()
    found: set[str] = set()
    _walk_formula_clocks(node, model_clocks, found)
    return tuple(sorted(found))


def _walk_formula_clocks(
    node: Expr, model_clocks: set[str], found: set[str]
) -> None:
    if isinstance(node, FreezeExpr):
        if node.clock not in model_clocks:
            found.add(node.clock)
    elif isinstance(node, SimpleTimeExpr):
        clock = _clock_from_constraint("".join(node.constraints))
        if clock and clock not in model_clocks:
            found.add(clock)
    elif isinstance(node, ClockExpr):
        clock = _clock_from_constraint(node.constraints)
        if clock and clock not in model_clocks:
            found.add(clock)

    for attr in ("operand", "left", "right", "subject"):
        child = getattr(node, attr, None)
        if child is not None:
            _walk_formula_clocks(child, model_clocks, found)


def extend_timed_cgs_clocks(tcgs, formula_clocks: tuple[str, ...]) -> None:
    """Append formula clocks to tcgs.clocks and clocks_dict (mutates tcgs)."""
    for name in formula_clocks:
        if name in tcgs.clocks_dict:
            continue
        tcgs.clocks.append(name)
        tcgs.clocks_dict[name] = len(tcgs.clocks_dict)
