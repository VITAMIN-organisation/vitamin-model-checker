import re

from ..timed_cgs import TimedCGS
from .DBM import DBM

"""
Kind of an ZoneGraph file to act as a utility for state-space exploration and bridge between 
DBM and timedCGS, is used by TCTL and other logics offering real-time verification of properties.
"""


def compute_zone_at(tcgs: TimedCGS, target: str, formulas: tuple[str]) -> DBM:
    """Computes the starting zone before the backwards reachability part.
    It is done using invariants and timing formulas
    """
    i = int(
        target[1]
    )  # Each element is a string "s0", "s1", ...,sn. We get the index here.
    dbm = DBM(len(tcgs.clocks))

    if len(tcgs.invariants_arr[i]) > 0:
        for k in range(0, len(tcgs.invariants_arr[i]), 2):
            clock, bound = tcgs.invariants_arr[i][k : k + 2]
            dbm.add_constraint(
                first_clock_idx=tcgs.clocks_dict[clock] + 1,
                second_clock_idx=0,
                constant=bound,
            )
    if formulas:
        bounds, _ = parse_constraints([formulas], tcgs.clocks_dict)
        for clock_index, op, bound in bounds:
            if op in ">=":
                dbm.add_constraint(
                    0, clock_index, -int(bound), op.replace(">", "<")
                )  # ex: x>2 == x-x0 > 2 == x0 - x < -2
            else:
                dbm.add_constraint(clock_index, 0, int(bound), op)
    return dbm


def add_constraints(tcgs: TimedCGS, current_zone: DBM, formulas: tuple[str]) -> DBM:
    formulas, _ = parse_constraints([formulas], tcgs.clocks_dict)
    z = current_zone.copy()
    for clock_index, op, bound in formulas:
        if op in ">=":
            z.add_constraint(
                0, clock_index, -int(bound), op.replace(">", "<")
            )  # ex: x>2 == x-x0 > 2 == x0 - x < -2
        else:
            z.add_constraint(clock_index, 0, int(bound), op)

    return z


def compute_predecessors(
    tcgs: TimedCGS, source: str, target: str, formulas: tuple[str]
) -> list[DBM]:
    """
    Computes the zone predecessors.
    Args:
        - tcgs: TimedConcurrentGameStructure representation of the game.
        - source: str, source location in the automaton.
        - target: str, target location in the automaton.
        - formulas: tuple[str], a tuple of time formulas: ('x ~ c'), ('&', ...), or ('|', ...)
    Returns:
        - A DBM if the formula is a conjunction or atomic, or a list of DBMs if the formula is a disjunction (OR).
    """
    if formulas is None or len(formulas) == 0:
        raise ValueError("There are no real-time formulas")
    formula_operator = formulas[0]
    # Base case
    if formula_operator not in ("or", "|", "&", "and"):
        dbm = compute_zone_at(tcgs, target, formulas)
        i, j = int(source[1]), int(target[1])
        constraints = [
            c.strip()
            for c in tcgs.clock_constraint_struct[i][j].split(",")
            if c.strip()
        ]
        # constraints.extend([formulas])
        bounds, resets = parse_constraints(constraints, tcgs.clocks_dict)

        for clock_index, _ in resets:
            dbm.free(clock_index)  # Perform inverse reset

        # Add the time constraints again after doing inverse reset
        for clock_index, op, bound in bounds:
            if op in ">=":
                dbm.add_constraint(
                    0, clock_index, -int(bound), op.replace(">", "<")
                )  # ex: x>2 == x-x0 > 2 == x0 - x < -2
            else:
                dbm.add_constraint(clock_index, 0, int(bound), op)

        # Apply invariants at source location
        if len(tcgs.invariants_arr[i]) > 0:
            for k in range(0, len(tcgs.invariants_arr[i]), 2):
                clock, bound = tcgs.invariants_arr[i][k : k + 2]
                dbm.add_constraint(
                    first_clock_idx=tcgs.clocks_dict[clock] + 1,
                    second_clock_idx=0,
                    constant=bound,
                )
        dbm.down()  # Time pre-decessor, i.e no lower bounds.
        return [dbm]

    # Handle AND/OR formulas
    subformulas = formulas[1:]

    if formula_operator in ("&", "and"):
        # Conjunction: flatten all subformulas into a single list
        flat_constraints = []
        for f in subformulas:
            if isinstance(f, tuple) and f[0] in ("&", "and"):
                # Nested AND: flatten recursively
                flat_constraints.extend(f[1:])
            else:
                flat_constraints.append(f)
        return compute_predecessors(tcgs, source, target, tuple(flat_constraints))
    elif formula_operator in ("|", "or"):
        # Disjunction: compute each branch and return a list of DBMs
        dbms = []
        for f in subformulas:
            res = compute_predecessors(
                tcgs, source, target, f if isinstance(f, tuple) else (f,)
            )
            if isinstance(res, list):
                dbms.extend(res)
            else:
                dbms.append(res)
        return dbms
    else:
        raise NotImplementedError(f"Unsupported binary operator: {formula_operator}")


def satisfied_at(tcgs: TimedCGS, source: str, target: str, formula: list[str]) -> bool:
    zone = compute_zone_at(tcgs, source, target)
    parsed_formula, _ = parse_constraints([formula], tcgs.clocks_dict)
    for clock_index, op, bound in parsed_formula:
        if op in ">=":
            zone.add_constraint(
                0, clock_index, -int(bound), op.replace(">", "<")
            )  # ex: x>2 == x-x0 > 2 == x0 - x < -2
        else:
            zone.add_constraint(clock_index, 0, int(bound), op)
    return not (zone.is_empty())


def parse_constraints(constraints: list[str], clocks_dict):
    bounds = []
    resets = []
    for constraint in filter(None, constraints):
        m_bound = re.match(r"(\w+)(>|<|>=|<=)(\d+)", constraint)
        m_reset = re.match(r"(\w+)=(\d+)", constraint)
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
    """
    Returns a list with the maximum constant each clock is compared to
    across all invariants and transition guards. The index of the list
    corresponds to the clock's index.

    Used for: k normalization
    """
    max_constants = [0] * (len(tcgs.clocks))

    for invariants in tcgs.invariants_arr:
        for i in range(0, len(invariants), 2):
            clock = invariants[i]
            value = int(invariants[i + 1])
            if clock in tcgs.clocks_dict:
                clock_idx = tcgs.clocks_dict[clock]
                if value > max_constants[clock_idx]:
                    max_constants[clock_idx] = value

    for row in tcgs.clock_constraint_struct:
        for constraint_str in row:
            if constraint_str:
                constraints = constraint_str.split(",")
                for constraint in constraints:
                    # Regex to find clock, operator, and value
                    match = re.search(
                        r"(\w+)\s*(?:==|>=|<=|>|<)\s*(\d+\.?\d*)", constraint
                    )
                    if match:
                        clock, value_str = match.groups()
                        if clock in tcgs.clocks_dict:
                            clock_idx = tcgs.clocks_dict[clock]
                            value = int(value_str)
                            if value > max_constants[clock_idx]:
                                max_constants[clock_idx] = value

    return max_constants
