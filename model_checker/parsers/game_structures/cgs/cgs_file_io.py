"""Writing CGS files: updated transition matrix or full update from a tree (NatATL)."""

from typing import Any, List


def write_updated_file(
    input_filename: str, modified_graph: List[List], output_filename: str
) -> None:
    """Copy the input file to output, replacing only the Transition section with the modified graph."""
    with open(input_filename, encoding="utf-8") as input_file, open(
        output_filename, "w", encoding="utf-8"
    ) as output_file:
        current_section = None
        matrix_row = 0

        for line in input_file:
            stripped_line = line.rstrip("\n\r")

            if stripped_line == "Transition":
                current_section = "Transition"
                output_file.write(stripped_line + "\n")
                continue

            if current_section == "Transition":
                if matrix_row < len(modified_graph):
                    output_file.write(
                        " ".join(map(str, modified_graph[matrix_row])) + "\n"
                    )
                    matrix_row += 1
                elif matrix_row == len(modified_graph):
                    current_section = None
                    output_file.write("Unknown_Transition_by\n")
                continue

            output_file.write(line)


def update_cgs_file(
    input_file: str,
    modified_file: str,
    tree: Any,
    tree_states: List[str],
    unwinded_CGS: List[List],
) -> None:
    """Write a new CGS file from the input, with transitions/states/labelling taken from the unwound tree.

    Used by NatATL Recall. tree must have label_row on nodes and a children list.
    """

    def read_input_file(file_path: str) -> List[str]:
        with open(file_path, encoding="utf-8") as file:
            return file.readlines()

    def write_output_file(file_path: str, lines: List[str]) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)

    def _splice(lines: List[str], start: int, end: int, new: List[str]) -> List[str]:
        return lines[:start] + new + lines[end:]

    def update_transitions(lines: List[str], new_transitions: List[str]) -> List[str]:
        try:
            transition_start = lines.index("Transition\n") + 1
        except ValueError as err:
            raise ValueError(
                "Required section 'Transition' not found in input file"
            ) from err

        if "Unknown_Transition_by\n" in lines:
            transition_end = lines.index("Unknown_Transition_by\n")
        elif "Name_State\n" in lines:
            transition_end = lines.index("Name_State\n")
        else:
            raise ValueError(
                "Could not find end of Transition section (missing 'Unknown_Transition_by' or 'Name_State')"
            )

        return _splice(lines, transition_start, transition_end, new_transitions)

    def update_name_state(lines: List[str], states: List[str]) -> List[str]:
        try:
            name_state_start = lines.index("Name_State\n") + 1
        except ValueError as err:
            raise ValueError(
                "Required section 'Name_State' not found in input file"
            ) from err

        try:
            initial_state_index = lines.index("Initial_State\n")
        except ValueError as err:
            raise ValueError(
                "Required section 'Initial_State' not found in input file"
            ) from err

        states_line = " ".join(states) + "\n"
        return _splice(lines, name_state_start, initial_state_index, [states_line])

    def update_labelling(lines: List[str], labelling: List[str]) -> List[str]:
        try:
            labelling_start = lines.index("Labelling\n") + 1
        except ValueError as err:
            raise ValueError(
                "Required section 'Labelling' not found in input file"
            ) from err

        try:
            num_agents_index = lines.index("Number_of_agents\n")
        except ValueError as err:
            raise ValueError(
                "Required section 'Number_of_agents' not found in input file"
            ) from err

        return _splice(lines, labelling_start, num_agents_index, labelling)

    lines = read_input_file(input_file)

    new_transitions = [" ".join(map(str, row)) + "\n" for row in unwinded_CGS]

    lines = update_transitions(lines, new_transitions)

    lines = update_name_state(lines, tree_states)

    labelling = []

    # Iterative traversal to avoid hitting Python recursion limits on deep trees.
    stack = [tree]
    while stack:
        node = stack.pop()
        labelling.append(" ".join(map(str, node.label_row)) + "\n")
        # Preserve original left-to-right depth-first order.
        if getattr(node, "children", None):
            stack.extend(reversed(node.children))

    lines = update_labelling(lines, labelling)

    write_output_file(modified_file, lines)
