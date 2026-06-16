"""Helpers for parsing section-based model files."""

import numpy as np

SECTION_HANDLERS = {
    "Transition": lambda data, line: data["graph"].append(line.split()),
    "Preorder": lambda data, line: data["preorder"].append(line.split()),
    "Name_State": lambda data, line: data["states"].extend(line.split()),
    "Initial_State": lambda data, line: data.update({"initial_state": line}),
    "Atomic_propositions": lambda data, line: data["atomic_propositions"].extend(
        line.split()
    ),
    "Labelling": lambda data, line: data["matrix_prop"].append(line.split()),
    "Number_of_agents": lambda data, line: data.update({"number_of_agents": int(line)}),
}


def parse_sectioned_lines(lines, section_handlers, data):
    """Apply section handlers to stripped file lines in order."""
    section = None
    for raw_line in lines:
        line = raw_line.strip()
        if line in section_handlers:
            section = line
            continue
        if section is not None:
            section_handlers[section](data, line)


def read_sectioned_model_file(
    filename,
    initial_data,
    section_handlers,
    extra_array_dtypes=None,
):
    """Load a sectioned model file and normalize common arrays and counters."""
    with open(filename, encoding="utf-8") as handle:
        lines = handle.readlines()

    data = initial_data.copy()
    parse_sectioned_lines(lines, section_handlers, data)

    data["states_counter"] = len(data["states"])
    data["atomic_propositions_counter"] = len(data["atomic_propositions"])
    data["graph"] = np.array(data["graph"])
    data["states"] = np.array(data["states"])
    data["atomic_propositions"] = np.array(data["atomic_propositions"])
    data["matrix_prop"] = np.array(data["matrix_prop"], dtype=int)

    if extra_array_dtypes is None:
        return data

    for key, dtype in extra_array_dtypes.items():
        data[key] = np.array(data[key], dtype=dtype)

    return data
