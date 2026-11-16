"""Clocks that only a timed formula names (freeze, guards); they join the model's
clocks before the region graph is built."""

from model_checker.parsers.game_structures.timed_cgs.constraint_syntax import (
    CLOCK_BOUND_PREFIX_RE,
)
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter


def _clock_from_constraint(text: str) -> str | None:
    match = CLOCK_BOUND_PREFIX_RE.match(str(text))
    return match.group(1) if match else None


def _is_freeze_node(node) -> bool:
    return (
        type(node).__name__ == "FreezeExpr"
        and getattr(node, "clock", None) is not None
        and getattr(node, "operand", None) is not None
    )


def collect_formula_clocks(node, model_clocks: set[str]) -> tuple[str, ...]:
    """Return freeze/guard clock names that appear in the formula but not the model."""
    if node is None:
        return ()
    found: set[str] = set()
    _walk_formula_clocks(node, model_clocks, found)
    return tuple(sorted(found))


def formula_clock_constants(node, clocks_dict: dict[str, int]) -> dict[str, int]:
    """The largest constant each clock is compared with in the formula's guards."""
    constants: dict[str, int] = {}
    if node is not None:
        names = {index + 1: clock for clock, index in clocks_dict.items()}
        _walk_formula_constants(node, clocks_dict, names, constants)
    return constants


def _walk_formula_constants(
    node, clocks_dict: dict[str, int], names: dict[int, str], constants: dict[str, int]
) -> None:
    constraints = getattr(node, "constraints", None)
    if constraints is not None:
        text = "".join(constraints) if isinstance(constraints, tuple) else constraints
        found, _ = DBMAdapter.parse_constraints([str(text)], clocks_dict)
        for clock_index, _op, constant in found:
            clock = names[clock_index]
            constants[clock] = max(constants.get(clock, 0), constant)

    for attr in ("operand", "left", "right", "formula", "subject"):
        child = getattr(node, attr, None)
        if child is not None:
            _walk_formula_constants(child, clocks_dict, names, constants)


def _walk_formula_clocks(node, model_clocks: set[str], found: set[str]) -> None:
    if _is_freeze_node(node):
        if node.clock not in model_clocks:
            found.add(node.clock)
    elif type(node).__name__ == "SimpleTimeExpr":
        clock = _clock_from_constraint("".join(node.constraints))
        if clock and clock not in model_clocks:
            found.add(clock)
    elif type(node).__name__ == "ClockExpr":
        clock = _clock_from_constraint(node.constraints)
        if clock and clock not in model_clocks:
            found.add(clock)

    for attr in ("operand", "left", "right", "formula", "subject"):
        child = getattr(node, attr, None)
        if child is not None:
            _walk_formula_clocks(child, model_clocks, found)


def extend_timed_cgs_clocks(tcgs, formula_clocks: tuple[str, ...]) -> None:
    """Register formula clocks on the timed model so zones can track them."""
    for name in formula_clocks:
        if name in tcgs.clocks_dict:
            continue
        tcgs.clocks.append(name)
        tcgs.clocks_dict[name] = len(tcgs.clocks_dict)
