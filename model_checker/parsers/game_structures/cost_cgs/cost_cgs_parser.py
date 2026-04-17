"""Parsing for costCGS model files.

Handles cost sections (Costs_for_actions, Costs_for_actions_split), transitions
with costs, and reuses the base CGS parser for common sections.
"""

from typing import Any, List

from model_checker.parsers.game_structures.cgs import cgs_parser


def parse_cost_sections(lines: List[str], instance: Any) -> None:
    """Parse cost sections and set usesCostsInsteadOfActions if Transition_With_Costs is seen.

    Args:
        lines: List of file lines (list of str).
        instance: costCGS instance to fill (cost_for_action, usesCostsInsteadOfActions).
    """
    current_section = None

    cost_section_headers = {
        "Costs_for_actions": "Costs_for_actions",
        "Costs_for_actions_split": "Costs_for_actions_split",
    }

    def process_costs_for_actions(line):
        if line:
            parse_costs_for_actions(line, instance)

    def process_costs_for_actions_split(line):
        if line:
            parse_costs_for_actions_split(line, instance)

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


def parse_costs_for_actions(line: str, instance: Any) -> None:
    """Parse one line from Costs_for_actions (single cost list per action-state).

    Args:
        line: One line of the Costs_for_actions section (str).
        instance: costCGS instance; cost_for_action is updated.
    """
    parse_cost_line(line, instance, parse_split=False)


def parse_costs_for_actions_split(line: str, instance: Any) -> None:
    """Parse one line from Costs_for_actions_split (nested cost lists per action-state).

    Args:
        line: One line of the Costs_for_actions_split section (str).
        instance: costCGS instance; cost_for_action is updated.
    """
    parse_cost_line(line, instance, parse_split=True)


def parse_cost_line(line: str, instance: Any, parse_split: bool = False) -> None:
    """Parse one cost line: action, state(s) and cost(s).

    Args:
        line: One cost line (str); format "action state$cost[:cost...]" with
            optional further state$cost groups separated by semicolons.
        instance: costCGS instance; cost_for_action is updated.
        parse_split: If True, costs are parsed as nested lists (e.g. [[1,2],[3]]).
    """
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

        key = instance.translate_action_and_state_to_key(action_name, state)
        instance.cost_for_action.update({key: costs})


def parse_common_sections(lines: List[str], instance: Any) -> None:
    """Fill states, labelling, initial_state, number_of_agents via base CGS parser.

    Skips Transition and cost sections. Call after parse_cost_sections.

    Args:
        lines: List of file lines (list of str).
        instance: costCGS instance to fill.
    """
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
    """Collect transition rows from Transition or Transition_With_Costs.

    Sets instance.usesCostsInsteadOfActions if Transition_With_Costs is seen.

    Args:
        lines: List of file lines (list of str).
        instance: costCGS instance; usesCostsInsteadOfActions may be set.

    Returns:
        List of rows (each row is a list of str or cost values).
    """
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
    """Build instance.graph from transition rows.

    Uses costs or actions depending on instance.usesCostsInsteadOfActions.
    Call after parse_cost_sections and parse_common_sections.

    Args:
        lines: List of file lines (list of str).
        instance: costCGS instance; graph and optionally actions are filled.
    """
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
    """Turn a raw transition row into a processed row.

    If instance.usesCostsInsteadOfActions, cells become 0 or str; otherwise
    uses base CGS row processing and appends to actions.

    Args:
        row: One transition row (list of str).
        actions: List to append action strings to (when not using costs).
        instance: costCGS instance (usesCostsInsteadOfActions).

    Returns:
        Processed row (list of int or str).
    """
    if instance.usesCostsInsteadOfActions:
        return [0 if item == "0" else str(item) for item in row]
    else:
        return cgs_parser.process_transition_row(row, actions)
