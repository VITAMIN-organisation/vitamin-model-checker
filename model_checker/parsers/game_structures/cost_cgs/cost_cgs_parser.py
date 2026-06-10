"""Parsing for costCGS model files.

Handles cost sections (Costs_for_actions, Costs_for_actions_split), transitions
with costs, and reuses the base CGS parser for common sections.
"""

from typing import Any, List

from model_checker.parsers.game_structures.cgs import cgs_parser


def parse_cost_sections(lines: List[str], instance: Any) -> None:
    """Read cost sections into instance.cost_for_action.

    Sets usesCostsInsteadOfActions when Transition_With_Costs appears.
    """
    current_section = None

    cost_section_headers = {
        "Costs_for_actions": "Costs_for_actions",
        "Costs_for_actions_split": "Costs_for_actions_split",
    }

    def process_costs_for_actions(line):
        if line:
            parse_cost_line(line, instance, parse_split=False)

    def process_costs_for_actions_split(line):
        if line:
            parse_cost_line(line, instance, parse_split=True)

    section_processors = {
        "Costs_for_actions": process_costs_for_actions,
        "Costs_for_actions_split": process_costs_for_actions_split,
    }

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line == "Transition_With_Costs":
            instance.usesCostsInsteadOfActions = True
            current_section = None
        elif line in cost_section_headers:
            current_section = cost_section_headers[line]
        elif line in cgs_parser.SECTION_HEADERS:
            current_section = None
        elif current_section and current_section in section_processors:
            section_processors[current_section](line)


def parse_cost_line(line: str, instance: Any, parse_split: bool = False) -> None:
    """Parse one line: action state$cost[:cost...] with optional ;-separated groups."""
    values = line.strip().split()
    if len(values) < 2:
        raise ValueError(
            f"Malformed cost line '{line}'. Expected 'action state$cost[:cost...]'."
        )

    action_name = values[0]
    state_and_cost_string = values[1].split(";")

    for couple in state_and_cost_string:
        if not couple:
            continue

        state_and_cost = couple.split("$", 1)
        if len(state_and_cost) != 2 or not state_and_cost[0] or not state_and_cost[1]:
            raise ValueError(
                f"Malformed cost entry '{couple}' in line '{line}'. "
                "Expected 'state$cost[:cost...]'."
            )

        state = state_and_cost[0]
        cost_string = state_and_cost[1]

        try:
            if parse_split:
                costs_res = cost_string.split(":")
                costs = [[int(cc) for cc in c.split(",")] for c in costs_res]
            else:
                costs = [int(c) for c in cost_string.split(":")]
        except ValueError as exc:
            raise ValueError(f"Invalid cost value in line '{line}': {exc}") from exc

        key = f"{action_name};{state}"
        instance.cost_for_action.update({key: costs})


def parse_common_sections(lines: List[str], instance: Any) -> None:
    """Load states, labels, and agents via the base CGS parser (no transition rows)."""
    sections_to_skip = {
        "Transition",
        "Transition_With_Costs",
        "Costs_for_actions",
        "Costs_for_actions_split",
    }
    filtered_lines = cgs_parser.filter_lines_for_common_sections(
        lines, sections_to_skip
    )
    cgs_parser.parse_cgs_file(filtered_lines, instance)


def extract_transition_rows(lines: List[str], instance: Any) -> List[Any]:
    """Collect rows from Transition or Transition_With_Costs."""
    current_section = None
    rows_graph = []

    transition_headers = {
        "Transition": "Transition",
        "Transition_With_Costs": "Transition",
    }

    for line in lines:
        stripped = line.strip()

        if stripped in transition_headers:
            current_section = transition_headers[stripped]
            if stripped == "Transition_With_Costs":
                instance.usesCostsInsteadOfActions = True
        elif stripped in cgs_parser.SECTION_HEADERS:
            current_section = None
        elif current_section == "Transition" and stripped:
            rows_graph.append(stripped.split())

    return rows_graph


def parse_transitions(lines: List[str], instance: Any) -> None:
    """Build instance.graph from transition rows (costs or actions)."""
    rows_graph = extract_transition_rows(lines, instance)
    if not rows_graph:
        return

    cgs_parser._check_rectangular_rows(rows_graph, "Transition")
    actions = []
    for row in rows_graph:
        processed_row = process_transition_row_with_costs(row, actions, instance)
        instance.graph.append(processed_row)

    if not instance.usesCostsInsteadOfActions:
        instance.actions = list(set(actions))


def process_transition_row_with_costs(
    row: List[Any], actions: List[Any], instance: Any
) -> List[Any]:
    """Process one transition row.

    With Transition_With_Costs, cells are 0 or a cost string; otherwise parse
    as standard CGS actions and collect names in actions.
    """
    if instance.usesCostsInsteadOfActions:
        return [0 if item == "0" else str(item) for item in row]
    else:
        return cgs_parser.process_transition_row(row, actions)
