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


def _parse_clocks(instance: Any, line: str) -> None:
    instance.clocks = line.split()
    instance.clock_constraints_dict = {clock: [] for clock in instance.clocks}
    instance.clocks_dict = {value: index for index, value in enumerate(instance.clocks)}


def _parse_clock_constraints_row(instance: Any, line: str, row: int) -> None:
    for col, constraint in enumerate(line.split()):
        for part in constraint.split(","):
            if re.search(r"(\w+)(=|>|>=|==|<|<=)(\d+)", part):
                cell = instance.clock_constraint_struct[row][col]
                if len(cell) > 1:
                    instance.clock_constraint_struct[row][col] = f"{cell},{part}"
                else:
                    instance.clock_constraint_struct[row][col] = str(part)


def _parse_invariants_row(instance: Any, line: str, location: int) -> None:
    for value in line.split():
        for invariant in value.split(","):
            if matched := re.match(r"(\w+)(?:<=|<)(\d+)", invariant):
                instance.invariants_arr[location] += [
                    matched.group(1),
                    float(matched.group(2)),
                ]
