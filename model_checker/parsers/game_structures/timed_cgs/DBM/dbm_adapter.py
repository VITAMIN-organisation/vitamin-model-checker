import re

from ..timed_cgs import TimedCGS
from .DBM import DBM

# Bridges timedCGS models and DBM zone operations.

FormulaInput = str | tuple[str, ...]
_AND_OPS = frozenset({"&", "and"})
_OR_OPS = frozenset({"|", "or"})
_COMBINATORS = _AND_OPS | _OR_OPS
_BOUND_RE = re.compile(r"(\w+)(>|<|>=|<=)(\d+)")
_RESET_RE = re.compile(r"(\w+)=(\d+)")
_MAX_CONSTRAINT_RE = re.compile(r"(\w+)\s*(?:==|>=|<=|>|<)\s*(\d+\.?\d*)")


def apply_bounds(dbm: DBM, bounds) -> None:
    for clock_index, op, bound in bounds:
        if op in ">=":
            dbm.add_constraint(0, clock_index, -int(bound), op.replace(">", "<"))
        else:
            dbm.add_constraint(clock_index, 0, int(bound), op)


def apply_location_invariants(dbm: DBM, tcgs: TimedCGS, location: int) -> None:
    for k in range(0, len(tcgs.invariants_arr[location]), 2):
        clock, bound = tcgs.invariants_arr[location][k : k + 2]
        dbm.add_constraint(
            first_clock_idx=tcgs.clocks_dict[clock] + 1,
            second_clock_idx=0,
            constant=bound,
        )


def zone_satisfies_guards(
    tcgs: TimedCGS,
    location: str,
    zone: DBM,
    guards,
    resets=None,
) -> bool:
    """True when guards (and optional resets) hold with location invariants."""
    candidate = zone.copy()
    apply_bounds(candidate, guards)
    if resets:
        for clock_idx, reset_value in resets:
            candidate.reset(clock_idx, reset_value)
    loc_idx = tcgs.get_index_by_state_name(location)
    if tcgs.invariants_arr[loc_idx]:
        apply_location_invariants(candidate, tcgs, loc_idx)
    return not candidate.is_empty()


def delay_zone(tcgs: TimedCGS, zone: DBM, location: str) -> DBM | None:
    """Time-delay successor zone at location, or None if empty."""
    loc_idx = tcgs.get_index_by_state_name(location)
    delay = zone.copy()
    delay.up()
    if tcgs.invariants_arr[loc_idx]:
        apply_location_invariants(delay, tcgs, loc_idx)
    return delay if not delay.is_empty() else None


def forward_transition_zone(
    tcgs: TimedCGS, zone: DBM, source_idx: int, target_idx: int
) -> DBM | None:
    """Zone after a discrete transition, or None if empty."""
    constraints = [
        part.strip()
        for part in tcgs.clock_constraint_struct[source_idx][target_idx].split(",")
        if part.strip()
    ]
    guards, resets = parse_constraints(constraints, tcgs.clocks_dict)
    successor = zone.copy()
    apply_bounds(successor, guards)
    if successor.is_empty():
        return None
    for clock_idx, reset_value in resets:
        successor.reset(clock_idx, reset_value)
    if resets:
        successor.up()
    if tcgs.invariants_arr[target_idx]:
        apply_location_invariants(successor, tcgs, target_idx)
    return successor if not successor.is_empty() else None


def _zone_at_target(tcgs: TimedCGS, target: str, formula_parts: list[str]) -> DBM:
    if not formula_parts:
        raise ValueError("There are no real-time formulas")
    dbm = DBM(len(tcgs.clocks))
    target_idx = int(target[1:])
    if tcgs.invariants_arr[target_idx]:
        apply_location_invariants(dbm, tcgs, target_idx)
    for part in formula_parts:
        bounds, _ = parse_constraints([part], tcgs.clocks_dict)
        apply_bounds(dbm, bounds)
    return dbm


def _backward_step_zone(tcgs: TimedCGS, source: str, target: str, dbm: DBM) -> DBM:
    source_idx = int(source[1:])
    target_idx = int(target[1:])
    bounds, resets = parse_constraints(
        [
            part.strip()
            for part in tcgs.clock_constraint_struct[source_idx][target_idx].split(",")
            if part.strip()
        ],
        tcgs.clocks_dict,
    )
    for clock_index, _ in resets:
        dbm.free(clock_index)
    apply_bounds(dbm, bounds)
    if tcgs.invariants_arr[source_idx]:
        apply_location_invariants(dbm, tcgs, source_idx)
    dbm.down()
    return dbm


def _atomic_formula_parts(formula: FormulaInput) -> list[str]:
    if isinstance(formula, str):
        return [formula]
    if isinstance(formula, tuple):
        if not formula:
            raise ValueError("There are no real-time formulas")
        if formula[0] in _COMBINATORS:
            raise ValueError("Expected an atomic clock formula")
        return [str(part) for part in formula]
    raise TypeError(f"Unsupported formula type: {type(formula)!r}")


def _flatten_and_parts(subformulas: tuple) -> list[str]:
    parts: list[str] = []
    for item in subformulas:
        if isinstance(item, tuple) and item and item[0] in _AND_OPS:
            parts.extend(_flatten_and_parts(item[1:]))
        elif isinstance(item, str):
            parts.append(item)
        elif isinstance(item, tuple) and item:
            parts.append(str(item[0]))
    return parts


def add_constraints(tcgs: TimedCGS, current_zone: DBM, formulas: FormulaInput) -> DBM:
    bounds, _ = parse_constraints(
        list(_atomic_formula_parts(formulas)), tcgs.clocks_dict
    )
    zone = current_zone.copy()
    apply_bounds(zone, bounds)
    return zone


def compute_predecessors(
    tcgs: TimedCGS,
    source: str,
    target: str,
    formulas: FormulaInput,
) -> list[DBM]:
    """Zone predecessors along source->target for the given clock formulas."""
    if formulas is None:
        raise ValueError("There are no real-time formulas")
    if isinstance(formulas, str):
        if not formulas:
            raise ValueError("There are no real-time formulas")
        if formulas[0] in _COMBINATORS:
            raise ValueError(f"Unsupported formula prefix: {formulas[0]!r}")
        zone = _zone_at_target(tcgs, target, [formulas])
        return [_backward_step_zone(tcgs, source, target, zone)]

    if not isinstance(formulas, tuple) or not formulas:
        raise ValueError("There are no real-time formulas")

    operator = formulas[0]
    if operator not in _COMBINATORS:
        zone = _zone_at_target(tcgs, target, _atomic_formula_parts(formulas))
        return [_backward_step_zone(tcgs, source, target, zone)]

    branches = formulas[1:]
    if operator in _AND_OPS:
        parts = _flatten_and_parts(branches)
        if not parts:
            raise ValueError("There are no real-time formulas")
        zone = _zone_at_target(tcgs, target, parts)
        return [_backward_step_zone(tcgs, source, target, zone)]

    result: list[DBM] = []
    for branch in branches:
        branch_input: FormulaInput = branch if isinstance(branch, tuple) else (branch,)
        result.extend(compute_predecessors(tcgs, source, target, branch_input))
    return result


def parse_constraints(constraints: list[str], clocks_dict):
    bounds = []
    resets = []
    for constraint in filter(None, constraints):
        m_bound = _BOUND_RE.match(constraint)
        m_reset = _RESET_RE.match(constraint)
        if m_bound:
            clock, op, bound = m_bound.groups()
            clock_index = clocks_dict[clock] + 1
            bounds.append((clock_index, op, int(bound)))
        elif m_reset:
            clock, bound = m_reset.groups()
            clock_index = clocks_dict[clock] + 1
            resets.append((clock_index, int(bound)))
    return bounds, resets


def get_max_clock_constraints(tcgs: TimedCGS) -> list[int]:
    """Per-clock max bound from invariants and transition guards."""
    max_constants = [0] * len(tcgs.clocks)
    clocks_dict = tcgs.clocks_dict

    for invariants in tcgs.invariants_arr:
        for clock, bound in zip(invariants[::2], invariants[1::2], strict=True):
            if clock in clocks_dict:
                idx = clocks_dict[clock]
                max_constants[idx] = max(max_constants[idx], int(bound))

    for constraint_str in (
        cell for row in tcgs.clock_constraint_struct for cell in row if cell
    ):
        for match in _MAX_CONSTRAINT_RE.finditer(constraint_str):
            clock, value_str = match.groups()
            if clock in clocks_dict:
                idx = clocks_dict[clock]
                max_constants[idx] = max(max_constants[idx], int(value_str))

    return max_constants
