"""Formula clocks Y for timed logics (disjoint from automaton clocks X)."""

import re

_CLOCK_BOUND_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_]*)(?:<=|>=|<|>)")


def _clock_from_constraint(text: str) -> str | None:
    match = _CLOCK_BOUND_RE.match(str(text))
    return match.group(1) if match else None


def _is_freeze_node(node) -> bool:
    return (
        type(node).__name__ == "FreezeExpr"
        and getattr(node, "clock", None) is not None
        and getattr(node, "operand", None) is not None
    )


def collect_formula_clocks(node, model_clocks: set[str]) -> tuple[str, ...]:
    """Collect formula clock names from a timed-logic AST."""
    if node is None:
        return ()
    found: set[str] = set()
    _walk_formula_clocks(node, model_clocks, found)
    return tuple(sorted(found))


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
    """Append formula clocks to tcgs.clocks and clocks_dict (mutates tcgs)."""
    for name in formula_clocks:
        if name in tcgs.clocks_dict:
            continue
        tcgs.clocks.append(name)
        tcgs.clocks_dict[name] = len(tcgs.clocks_dict)
