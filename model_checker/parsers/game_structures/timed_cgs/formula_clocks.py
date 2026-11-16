"""Clocks that only a timed formula names (freeze, guards); they join the model's
clocks before the region graph is built."""

from collections.abc import Iterator

from model_checker.parsers.game_structures.timed_cgs.constraint_syntax import (
    CLOCK_BOUND_PREFIX_RE,
)
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter

_CHILD_ATTRS = ("operand", "left", "right", "formula", "subject")


def ast_children(node) -> Iterator:
    """The subformula nodes of ``node``."""
    for attr in _CHILD_ATTRS:
        child = getattr(node, attr, None)
        if child is not None:
            yield child


def _nodes(node) -> Iterator:
    """``node`` and every node below it."""
    if node is None:
        return
    yield node
    for child in ast_children(node):
        yield from _nodes(child)


def _is_freeze_node(node) -> bool:
    return (
        type(node).__name__ == "FreezeExpr"
        and getattr(node, "clock", None) is not None
        and getattr(node, "operand", None) is not None
    )


def _constraint_text(node) -> str | None:
    """The clock constraint of a guard node, such as ``x<=3``, if it has one."""
    constraints = getattr(node, "constraints", None)
    if constraints is None:
        return None
    return "".join(constraints) if isinstance(constraints, tuple) else str(constraints)


def _named_clock(node) -> str | None:
    """The clock a freeze or clock constraint node names, if any."""
    if _is_freeze_node(node):
        return node.clock
    text = _constraint_text(node)
    if text is None:
        return None
    match = CLOCK_BOUND_PREFIX_RE.match(text)
    return match.group(1) if match else None


def collect_formula_clocks(node, model_clocks: set[str]) -> tuple[str, ...]:
    """Return freeze/guard clock names that appear in the formula but not the model."""
    found = {clock for child in _nodes(node) if (clock := _named_clock(child))}
    return tuple(sorted(found - model_clocks))


def formula_freeze_clocks(node) -> tuple[str, ...]:
    """The clocks the formula's freezes reset, sorted."""
    return tuple(
        sorted({child.clock for child in _nodes(node) if _is_freeze_node(child)})
    )


def formula_clock_constants(node, clocks_dict: dict[str, int]) -> dict[str, int]:
    """The largest constant each clock is compared with in the formula's guards."""
    constants: dict[str, int] = {}
    names = {index + 1: clock for clock, index in clocks_dict.items()}
    for child in _nodes(node):
        text = _constraint_text(child)
        if text is None:
            continue
        found, _ = DBMAdapter.parse_constraints([text], clocks_dict)
        for clock_index, _op, constant in found:
            clock = names[clock_index]
            constants[clock] = max(constants.get(clock, 0), constant)
    return constants


def extend_timed_cgs_clocks(tcgs, formula_clocks: tuple[str, ...]) -> None:
    """Register formula clocks on the timed model so zones can track them."""
    for name in formula_clocks:
        if name in tcgs.clocks_dict:
            continue
        tcgs.clocks.append(name)
        tcgs.clocks_dict[name] = len(tcgs.clocks_dict)
