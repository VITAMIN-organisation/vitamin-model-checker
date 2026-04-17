"""Parsing of CGS model files.

Reads section headers, builds transition and labelling matrices, and fills a CGS instance.
"""

import warnings

import numpy as np

# --- Constants ---

SECTION_HEADERS = frozenset(
    {
        "Transition",
        "Unknown_Transition_by",
        "Name_State",
        "Initial_State",
        "Atomic_propositions",
        "Labelling",
        "Number_of_agents",
    }
)

EXTENSION_SECTION_HEADERS = frozenset(
    {
        "Costs_for_actions",
        "Costs_for_actions_split",
        "Transition_With_Costs",
        "Capacities",
        "Capacities_assignment",
        "Actions_for_capacities",
    }
)


# --- Row Processing Functions ---


def process_transition_row(row, actions):
    """Turn a raw transition row into a processed row: "0" becomes int 0, rest stay as strings.

    Appends any comma-separated action strings into the actions list (in place).
    """
    new_row = []
    for item in row:
        if item == "0":
            new_row.append(0)
        else:
            item_str = str(item)
            new_row.append(item_str)
            # Extract actions from comma-separated values
            actions.extend(item_str.split(","))
    return new_row


def _check_rectangular_rows(rows, section_name):
    """Check that every row has the same length. Raises ValueError with 'inhomogeneous' if not."""
    if not rows:
        return
    first_len = len(rows[0])
    for i, row in enumerate(rows[1:], start=1):
        if len(row) != first_len:
            raise ValueError(
                f"The requested array has an inhomogeneous shape: "
                f"{section_name} row 0 has {first_len} column(s), "
                f"row {i} has {len(row)} column(s)."
            )


def process_labelling_row(row, row_index=None):
    """Convert a labelling row: "0" and "1" become ints. Raises ValueError if any other value appears.

    row_index is optional and only used to make error messages clearer.
    """
    processed_row = []
    for col_index, item in enumerate(row):
        if item == "0":
            processed_row.append(0)
        elif item == "1":
            processed_row.append(1)
        else:
            # Build error message with location information
            location = ""
            if row_index is not None:
                location = f" at row {row_index}, column {col_index}"
            raise ValueError(
                f"Invalid labelling matrix value: '{item}'{location}. "
                "Labelling matrix must contain only binary values (0 or 1)."
            )
    return processed_row


# --- Section Filtering and Extraction Helpers ---


def filter_lines_for_common_sections(lines, sections_to_skip):
    """Drop lines that belong to the given section headers; keep the rest.

    Used by capCGS and costCGS so they can parse only the common CGS sections.
    """
    filtered_lines = []
    current_section_to_skip = None

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        if stripped in sections_to_skip:
            current_section_to_skip = stripped
            continue

        if current_section_to_skip:
            if stripped in SECTION_HEADERS:
                current_section_to_skip = None
                filtered_lines.append(line)
            continue

        filtered_lines.append(line)

    return filtered_lines


def extract_transition_rows(lines, additional_transition_headers=None):
    """Collect all lines that are transition rows (between Transition and the next section).

    You can pass additional_transition_headers (e.g. {"Transition_With_Costs"}) so those
    sections are treated as transition sections too.
    """
    current_section = None
    rows_graph = []
    transition_headers = {"Transition"}
    if additional_transition_headers:
        transition_headers.update(additional_transition_headers)

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        if stripped in transition_headers:
            current_section = "Transition"
        elif stripped in SECTION_HEADERS:
            current_section = None
        elif current_section == "Transition" and stripped:
            rows_graph.append(stripped.split())

    return rows_graph


# --- Section Collection and Application ---


def _warn_duplicate_section(section_name):
    """Emit a warning for a duplicate section header."""
    messages = {
        "Initial_State": (
            "Duplicate 'Initial_State' section detected. "
            "Previous value will be overwritten with the last occurrence."
        ),
        "Number_of_agents": (
            "Duplicate 'Number_of_agents' section detected. "
            "Previous value will be overwritten with the last occurrence."
        ),
        "Name_State": (
            "Duplicate 'Name_State' section detected. "
            "States will be accumulated and deduplicated."
        ),
        "Atomic_propositions": (
            "Duplicate 'Atomic_propositions' section detected. "
            "Propositions will be accumulated and deduplicated."
        ),
    }
    msg = messages.get(section_name)
    if msg:
        warnings.warn(msg, UserWarning, stacklevel=3)


def _collect_section_data(lines, instance):
    """Run the section loop; return (states_list, atomic_propositions_list, rows_graph, rows_prop, actions).

    Sets instance.initial_state and instance.number_of_agents as side effects.
    """
    current_section = None
    rows_graph = []
    rows_unknown = []
    rows_prop = []
    states_list = []
    atomic_propositions_list = []
    actions = []
    seen_sections = set()

    def process_transition(line):
        if line:
            values = line.split()
            if values:
                rows_graph.append(values)

    def process_name_state(line):
        if line:
            values = line.split()
            if values:
                states_list.extend(values)

    def process_initial_state(line):
        if line and "$" not in line and ";" not in line:
            instance.initial_state = line

    def process_atomic_propositions(line):
        if line:
            values = line.split()
            if values:
                atomic_propositions_list.extend(values)

    def process_labelling(line):
        if line:
            values = line.split()
            if values:
                rows_prop.append(values)

    def process_number_of_agents(line):
        if line and line.strip():
            raw = line.strip()
            try:
                instance.number_of_agents = int(raw)
            except ValueError:
                raise ValueError(
                    f"Invalid value for Number_of_agents: '{raw}'. Expected a valid integer."
                ) from None

    section_processors = {
        "Transition": process_transition,
        "Unknown_Transition_by": lambda line: (
            rows_unknown.append(line.split()) if line else None
        ),
        "Name_State": process_name_state,
        "Initial_State": process_initial_state,
        "Atomic_propositions": process_atomic_propositions,
        "Labelling": process_labelling,
        "Number_of_agents": process_number_of_agents,
    }

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line in EXTENSION_SECTION_HEADERS:
            current_section = None
            continue
        if line in SECTION_HEADERS:
            current_section = line
            if current_section in seen_sections:
                _warn_duplicate_section(current_section)
            seen_sections.add(current_section)
            continue

        if current_section and current_section in section_processors:
            section_processors[current_section](line)

    return (
        states_list,
        atomic_propositions_list,
        rows_graph,
        rows_unknown,
        rows_prop,
        actions,
    )


def _apply_states(instance, states_list):
    """Validate and assign states_list to instance.states (deduplicated)."""
    if not states_list:
        instance.states = np.array([])
        return
    for i, state in enumerate(states_list):
        if isinstance(state, (list, tuple)):
            raise ValueError(
                "The requested array has an inhomogeneous shape: "
                f"Name_State element at index {i} is a sequence (list/tuple), "
                "expected scalar state names."
            )
    seen = set()
    unique = []
    for state in states_list:
        if state not in seen:
            seen.add(state)
            unique.append(state)
    instance.states = np.array(unique)


def _apply_atomic_propositions(instance, atomic_propositions_list):
    """Validate and assign atomic_propositions_list to instance.atomic_propositions (deduplicated)."""
    if not atomic_propositions_list:
        instance.atomic_propositions = np.array([])
        return
    for i, prop in enumerate(atomic_propositions_list):
        if isinstance(prop, (list, tuple)):
            raise ValueError(
                "The requested array has an inhomogeneous shape: "
                f"Atomic_propositions element at index {i} is a sequence "
                "(list/tuple), expected scalar names."
            )
    seen = set()
    unique = []
    for prop in atomic_propositions_list:
        if prop not in seen:
            seen.add(prop)
            unique.append(prop)
    instance.atomic_propositions = np.array(unique)


def _apply_graph_and_actions(instance, rows_graph, actions):
    """Assign transition matrix and actions list to instance."""
    if not rows_graph:
        instance.graph = []
        instance.actions = list(set(actions))
        return
    _check_rectangular_rows(rows_graph, "Transition")
    instance.graph = [process_transition_row(row, actions) for row in rows_graph]
    instance.actions = list(set(actions))


def _apply_labelling(instance, rows_prop):
    """Validate and assign labelling matrix to instance."""
    if not rows_prop:
        instance.matrix_prop = np.array([])
        return
    _check_rectangular_rows(rows_prop, "Labelling")
    # Process each row to ensure valid binary values and populate matrix_prop
    instance.matrix_prop = [
        process_labelling_row(row, i) for i, row in enumerate(rows_prop)
    ]


def _apply_unknown_transitions(instance, rows_unknown):
    """Validate and assign unknown transition matrix to instance."""
    if not rows_unknown:
        instance.unknown_transition_matrix = []
        return
    _check_rectangular_rows(rows_unknown, "Unknown_Transition_by")
    instance.unknown_transition_matrix = [
        [str(val) for val in row] for row in rows_unknown
    ]


def parse_cgs_file(lines, instance):
    """Read the given file lines and fill the CGS instance: states, graph, labelling, etc."""
    (
        states_list,
        atomic_propositions_list,
        rows_graph,
        rows_unknown,
        rows_prop,
        actions,
    ) = _collect_section_data(lines, instance)
    _apply_states(instance, states_list)
    _apply_atomic_propositions(instance, atomic_propositions_list)
    _apply_graph_and_actions(instance, rows_graph, actions)
    _apply_labelling(instance, rows_prop)
    _apply_unknown_transitions(instance, rows_unknown)
