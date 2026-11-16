import math

from ..constraint_syntax import BOUND_RE, MAX_CONSTRAINT_RE, RESET_RE
from ..timed_cgs import TimedCGS
from .bound import Bound
from .DBM import DBM

# Bridges timedCGS models and DBM zone operations.

FormulaInput = str | tuple[str, ...]
_AND_OPS = frozenset({"&", "and"})
_OR_OPS = frozenset({"|", "or"})
_COMBINATORS = _AND_OPS | _OR_OPS


def apply_bounds(dbm: DBM, bounds) -> None:
    for clock_index, op, bound in bounds:
        if op == "==":
            dbm.add_constraint(0, clock_index, -int(bound), "<=")
            dbm.add_constraint(clock_index, 0, int(bound), "<=")
        elif op in (">", ">="):
            dbm.add_constraint(0, clock_index, -int(bound), op.replace(">", "<"))
        else:
            dbm.add_constraint(clock_index, 0, int(bound), op)


def apply_location_invariants(dbm: DBM, tcgs: TimedCGS, location: int) -> None:
    apply_bounds(
        dbm,
        [
            (tcgs.clocks_dict[clock] + 1, op, bound)
            for clock, op, bound in tcgs.invariants_arr[location]
        ],
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


_STRICTNESS_FLIP = {"<": "<=", "<=": "<"}


def split_into_regions(zone: DBM, max_constants: list[int]) -> list[DBM]:
    """The clock regions that make up ``zone``, normalized against each clock's
    largest constant in ``max_constants``."""
    ceilings = [0, *max_constants]
    clocks = range(1, len(ceilings))
    parts = [zone]
    for i in clocks:
        parts = [piece for part in parts for piece in _cut(part, i, 0, 0, ceilings[i])]
    for i in clocks:
        for j in range(i + 1, len(ceilings)):
            parts = [
                piece
                for part in parts
                for piece in _cut_difference(part, i, j, ceilings)
            ]
    return parts


def _cut_difference(zone: DBM, i: int, j: int, ceilings: list[int]) -> list[DBM]:
    """``zone`` cut on ``x_i - x_j``, which matters only while both clocks are at
    most their largest constant (a normalized zone has no finite bound above it)."""
    if (
        zone.elements[i][0].constant > ceilings[i]
        or zone.elements[j][0].constant > ceilings[j]
    ):
        return [zone]
    return _cut(zone, i, j, -ceilings[j], ceilings[i])


def _cut(zone: DBM, i: int, j: int, low: int, high: int) -> list[DBM]:
    """``zone`` cut on ``x_i - x_j`` against every integer from ``low`` to ``high``
    that falls inside its range, each side strict and non-strict."""
    lower = -zone.elements[j][i].constant
    upper = zone.elements[i][j].constant
    first = low if math.isinf(lower) else max(low, math.floor(lower))
    last = high if math.isinf(upper) else min(high, math.ceil(upper))
    done: list[DBM] = []
    rest = zone
    for constant in range(first, last + 1):
        for op in ("<", "<="):
            # Constants rise, so only the part above this cut can meet the next.
            *below, rest = _sides(rest, i, j, constant, op)
            done += below
    return [*done, rest]


def _sides(zone: DBM, i: int, j: int, constant: int, op: str) -> list[DBM]:
    """The non-empty parts of ``zone`` where ``x_i - x_j op constant`` holds, then
    fails; ``zone`` itself when it lies on one side."""
    inside = Bound(constant, op)
    outside = Bound(-constant, _STRICTNESS_FLIP[op])
    if not inside.less_than(zone.elements[i][j]) or not outside.less_than(
        zone.elements[j][i]
    ):
        return [zone]
    pieces = []
    for first, second, side in ((i, j, inside), (j, i, outside)):
        piece = zone.copy()
        piece.add_constraint(first, second, side.constant, side.operator)
        if not piece.is_empty():
            pieces.append(piece)
    return pieces


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
    if tcgs.invariants_arr[target_idx]:
        apply_location_invariants(successor, tcgs, target_idx)
    return successor if not successor.is_empty() else None


def _zone_at_target(tcgs: TimedCGS, target: str, formula_parts: list[str]) -> DBM:
    if not formula_parts:
        raise ValueError("There are no real-time formulas")
    dbm = DBM(len(tcgs.clocks))
    target_idx = tcgs.get_index_by_state_name(target)
    if tcgs.invariants_arr[target_idx]:
        apply_location_invariants(dbm, tcgs, target_idx)
    for part in formula_parts:
        bounds, _ = parse_constraints([part], tcgs.clocks_dict)
        apply_bounds(dbm, bounds)
    return dbm


def _backward_step_zone(tcgs: TimedCGS, source: str, target: str, dbm: DBM) -> DBM:
    source_idx = tcgs.get_index_by_state_name(source)
    target_idx = tcgs.get_index_by_state_name(target)
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
        m_bound = BOUND_RE.match(constraint)
        m_reset = RESET_RE.match(constraint)
        if m_bound:
            clock, op, bound = m_bound.groups()
            if clock not in clocks_dict:
                raise ValueError(
                    f"Unknown clock '{clock}' in constraint '{constraint}'. "
                    f"Known clocks: {list(clocks_dict)}."
                )
            clock_index = clocks_dict[clock] + 1
            bounds.append((clock_index, op, int(bound)))
        elif m_reset:
            clock, bound = m_reset.groups()
            if clock not in clocks_dict:
                raise ValueError(
                    f"Unknown clock '{clock}' in reset '{constraint}'. "
                    f"Known clocks: {list(clocks_dict)}."
                )
            clock_index = clocks_dict[clock] + 1
            resets.append((clock_index, int(bound)))
        else:
            raise ValueError(
                f"Unrecognized constraint token '{constraint}'. "
                "Expected format: <clock><op><integer> (bound) or <clock>=<integer> (reset)."
            )
    return bounds, resets


def get_max_clock_constraints(tcgs: TimedCGS) -> list[int]:
    """Per-clock max bound from invariants and transition guards."""
    max_constants = [0] * len(tcgs.clocks)
    clocks_dict = tcgs.clocks_dict

    for invariants in tcgs.invariants_arr:
        for clock, _op, bound in invariants:
            if clock in clocks_dict:
                idx = clocks_dict[clock]
                max_constants[idx] = max(max_constants[idx], int(bound))

    for constraint_str in (
        cell for row in tcgs.clock_constraint_struct for cell in row if cell
    ):
        for match in MAX_CONSTRAINT_RE.finditer(constraint_str):
            clock, value_str = match.groups()
            if clock in clocks_dict:
                idx = clocks_dict[clock]
                max_constants[idx] = max(max_constants[idx], int(value_str))

    return max_constants
