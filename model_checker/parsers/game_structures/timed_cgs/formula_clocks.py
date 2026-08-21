"""Formula clocks introduced by timed formulas (freeze / real-time guards).

These clocks are not part of the automaton declaration; they are added to the
timedCGS before the zone graph is built so freeze quantification can be evaluated.
"""

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
    """Return freeze/guard clock names that appear in the formula but not the model."""
    if node is None:
        return ()
    found: set[str] = set()
    _walk_formula_clocks(node, model_clocks, found)
    return tuple(sorted(found))


_BOUND_CONSTANT_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9_]*)\s*(?:<=|>=|<|>|==)\s*(\d+)")


def max_constants_from_formula(node, clocks_dict: dict[str, int]) -> list[int]:
    """Largest constant per clock used in formula guards.

    Needed so zone extrapolation keeps distinctions required by the formula,
    not only those present in automaton invariants and transition guards.
    """
    maxima = [0] * len(clocks_dict)
    if node is None:
        return maxima
    _walk_formula_max_constants(node, clocks_dict, maxima)
    return maxima


def _record_constraint_maxima(
    text: str, clocks_dict: dict[str, int], maxima: list[int]
) -> None:
    for clock, value_str in _BOUND_CONSTANT_RE.findall(str(text)):
        if clock in clocks_dict:
            idx = clocks_dict[clock]
            maxima[idx] = max(maxima[idx], int(value_str))


def _walk_formula_max_constants(
    node, clocks_dict: dict[str, int], maxima: list[int]
) -> None:
    constraints = getattr(node, "constraints", None)
    if constraints is not None:
        if isinstance(constraints, tuple):
            _record_constraint_maxima("".join(constraints), clocks_dict, maxima)
        else:
            _record_constraint_maxima(str(constraints), clocks_dict, maxima)

    for attr in ("operand", "left", "right", "formula", "subject"):
        child = getattr(node, attr, None)
        if child is not None:
            _walk_formula_max_constants(child, clocks_dict, maxima)


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
