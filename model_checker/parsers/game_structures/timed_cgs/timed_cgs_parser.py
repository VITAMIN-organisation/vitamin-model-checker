"""timedCGS file parsing."""

import re
from typing import Any

from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser

TIMED_SECTION_HEADERS = frozenset(
    {
        "Clocks",
        "Clock_constraints",
        "Invariants",
    }
)


def parse_base_sections(lines: list[str], instance: Any) -> None:
    cost_cgs_parser.parse_cost_sections(lines, instance)
    cost_cgs_parser.parse_common_sections(lines, instance)
    cost_cgs_parser.parse_transitions(lines, instance)


def parse_timed_sections(lines: list[str], instance: Any) -> None:
    state_count = len(instance.states)
    instance.clock_constraint_struct = [[""] * state_count for _ in range(state_count)]
    instance.invariants_arr = [[] for _ in range(state_count)]

    current_section = None
    row_index = 0

    for line in lines:
        stripped = line.strip()
        if row_index >= state_count:
            row_index = 0

        if stripped == "Clocks":
            current_section = "Clocks"
        elif stripped == "Clock_constraints":
            current_section = "Clock_constraints"
        elif stripped == "Invariants":
            current_section = "Invariants"
        elif not stripped:
            continue
        elif current_section == "Clocks":
            _parse_clocks(instance, stripped)
        elif current_section == "Clock_constraints":
            _parse_clock_constraints_row(instance, stripped, row_index)
            row_index += 1
        elif current_section == "Invariants":
            _parse_invariants_row(instance, stripped, row_index)
            row_index += 1


_CONSTRAINT_RE = re.compile(r"^(\w+)(>=|<=|==|>|<|=)(\d+)$")
_INVARIANT_RE = re.compile(r"^(\w+)(<=|<)(\d+)$")
# Tokens that represent "no constraint on this transition cell"
_NO_CONSTRAINT_TOKENS = frozenset({"0", "-", "*"})


def _parse_clocks(instance: Any, line: str) -> None:
    instance.clocks = line.split()
    instance.clock_constraints_dict = {clock: [] for clock in instance.clocks}
    instance.clocks_dict = {value: index for index, value in enumerate(instance.clocks)}


def _parse_clock_constraints_row(instance: Any, line: str, row: int) -> None:
    for col, token in enumerate(line.split()):
        for part in token.split(","):
            part = part.strip()
            if not part or part in _NO_CONSTRAINT_TOKENS:
                continue
            if not _CONSTRAINT_RE.match(part):
                raise ValueError(
                    f"Malformed clock constraint '{part}' at row {row}, column {col}. "
                    "Expected format: <clock><op><integer> (e.g. x>=3, y<2)."
                )
            cell = instance.clock_constraint_struct[row][col]
            if len(cell) > 1:
                instance.clock_constraint_struct[row][col] = f"{cell},{part}"
            else:
                instance.clock_constraint_struct[row][col] = part


def _parse_invariants_row(instance: Any, line: str, location: int) -> None:
    for value in line.split():
        for invariant in value.split(","):
            invariant = invariant.strip()
            if not invariant or invariant in _NO_CONSTRAINT_TOKENS:
                continue
            matched = _INVARIANT_RE.match(invariant)
            if not matched:
                raise ValueError(
                    f"Malformed invariant '{invariant}' at location {location}. "
                    "Invariants must use '<' or '<=' (e.g. x<=5). "
                    "Use '>=' guards in Clock_constraints, not in Invariants."
                )
            instance.invariants_arr[location] += [
                matched.group(1),
                float(matched.group(3)),
            ]
