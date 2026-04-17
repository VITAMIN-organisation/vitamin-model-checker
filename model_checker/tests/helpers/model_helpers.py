"""Model loading, assertions, and content builders for tests in a single module."""

import ast
from pathlib import Path

import pytest

from model_checker.models.model_factory import create_model_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import costCGS


def assert_parse_structure(result, expected_structure=None, description=""):
    """Assert that parse result has correct structure."""
    assert result is not None, f"Parse result should not be None: {description}"

    if isinstance(result, str):
        return

    assert isinstance(
        result, tuple
    ), f"Parse result should be a tuple, got {type(result).__name__}: {description}"

    assert (
        len(result) >= 2
    ), f"Parse result tuple should have at least 2 elements, got {len(result)}: {description}"


def load_test_model(test_data_dir, model_path: str):
    """Load a model by path string (e.g. 'CGS/ATL/file.txt' or 'invalid/missing_name_state.txt'); pytest.fail on error.

    Paths under 'invalid/' or 'edge_cases/' are resolved under test_data_dir/tests/.
    The returned parser has .filename set; use parser.filename when calling
    APIs that expect a path string (e.g. model_checking(formula, path)).
    """
    path_parts = model_path.split("/")
    if len(path_parts) >= 2 and path_parts[0] in ("CGS", "costCGS", "capCGS"):
        file_path = test_data_dir / Path(*path_parts)
    elif path_parts and path_parts[0] in ("invalid", "edge_cases"):
        file_path = test_data_dir / "tests" / Path(*path_parts)
    else:
        file_path = test_data_dir / Path(*path_parts)
    path_str = str(file_path)
    try:
        parser = create_model_parser(path_str)
        parser.read_file(path_str)
        parser.filename = path_str
        return parser
    except Exception as e:
        pytest.fail(
            f"Failed to load model {model_path}\n"
            f"Error type: {type(e).__name__}\n"
            f"Error message: {str(e)}"
        )


def load_cgs_from_content(temp_file, content):
    """Load CGS from string content via a temp file."""
    parser = CGS()
    file_path = temp_file(content)
    parser.filename = str(file_path)
    parser.read_file(file_path)
    return parser


def load_costcgs_from_content(temp_file, content):
    """Load costCGS from string content via a temp file."""
    parser = costCGS()
    file_path = temp_file(content)
    parser.read_file(file_path)
    return parser


def extract_states_from_result(result):
    """Parse "Result: {state_set}" from model_checking dict; returns set or None."""
    if "error" in result:
        return None
    res_str = result.get("res", "")
    if "Result:" not in res_str:
        return None
    states_str = res_str.split("Result:")[1].strip()
    try:
        states = ast.literal_eval(states_str)
        if isinstance(states, set):
            return states
        if isinstance(states, (list, tuple)):
            return set(states)
        return None
    except (ValueError, SyntaxError, TypeError):
        return None


def build_cgs_model_content(
    transitions,
    state_names,
    initial_state,
    labelling,
    num_agents=2,
    prop_names=None,
    costs_for_actions=None,
    capacities=None,
    capacities_assignment=None,
    actions_for_capacities=None,
    unknown_transitions=None,
):
    """Assemble model file string for CGS, costCGS (costs_for_actions), or capCGS (capacities, etc.)."""
    if prop_names is None:
        prop_names = ["p"]
    transition_lines = [" ".join(row) for row in transitions]
    labelling_lines = [
        " ".join(row) if isinstance(row, list) else str(row) for row in labelling
    ]
    content_parts = ["Transition", chr(10).join(transition_lines)]
    if unknown_transitions is not None:
        unknown_lines = [" ".join(row) for row in unknown_transitions]
        content_parts.extend(["Unknown_Transition_by", chr(10).join(unknown_lines)])
    content_parts.extend(
        [
            "Name_State",
            " ".join(state_names),
            "Initial_State",
            initial_state,
        ]
    )
    if costs_for_actions is not None:
        costs_lines = [f"{a} {s}" for a, s in costs_for_actions.items()]
        content_parts.extend(["Costs_for_actions", chr(10).join(costs_lines)])
    content_parts.extend(
        [
            "Atomic_propositions",
            " ".join(prop_names),
            "Labelling",
            chr(10).join(labelling_lines),
        ]
    )
    if capacities is not None:
        content_parts.extend(["Capacities", " ".join(capacities)])
    if capacities_assignment is not None:
        capacity_lines = [
            " ".join(row) if isinstance(row, list) else str(row)
            for row in capacities_assignment
        ]
        content_parts.extend(["Capacities_assignment", chr(10).join(capacity_lines)])
    if actions_for_capacities is not None:
        action_capacity_lines = [
            f"{cap} {' '.join(acts)}" for cap, acts in actions_for_capacities.items()
        ]
        content_parts.extend(
            ["Actions_for_capacities", chr(10).join(action_capacity_lines)]
        )
    content_parts.extend(["Number_of_agents", str(num_agents)])
    return chr(10).join(content_parts) + chr(10)


def generate_linear_chain(
    num_states,
    num_agents=2,
    prop_names=None,
    dense_p=False,
    action_label="1",
):
    """Linear chain s0 -> s1 -> ... -> sN-1. Uses build_cgs_model_content.

    action_label: "1" for simple numeric transitions (scalability, NatATL);
      "AC" for CGS-style action strings with Unknown_Transition_by (ATL, CTL).
    dense_p: when True, p on all but last state (for Until).
    """
    if prop_names is None:
        prop_names = ["p"]
    state_names = [f"s{i}" for i in range(num_states)]
    use_ac = action_label == "AC"
    if use_ac:
        action = "AC" * num_agents if num_agents == 2 else "AC"
    transitions = []
    unknown_transitions = [] if use_ac else None
    for i in range(num_states):
        row = ["0"] * num_states
        if i == num_states - 1:
            row[i] = "*" if use_ac else "1"
        elif i + 1 < num_states:
            row[i + 1] = action if use_ac else "1"
        transitions.append(row)
        if use_ac:
            unknown_transitions.append(["0"] * num_states)
    labelling = []
    for i in range(num_states):
        row = []
        for prop in prop_names:
            if prop == "p":
                row.append(
                    "1"
                    if (dense_p and i < num_states - 1)
                    or (not dense_p and (i == 0 or i == num_states - 1))
                    else "0"
                )
            elif prop == "q":
                row.append("1" if i == num_states - 1 else "0")
            else:
                row.append("0")
        labelling.append(row)
    return build_cgs_model_content(
        transitions=transitions,
        state_names=state_names,
        initial_state="s0",
        prop_names=prop_names,
        labelling=labelling,
        num_agents=num_agents,
        unknown_transitions=unknown_transitions,
    )


def generate_cycle_model(num_states, num_agents=2, prop_name="p"):
    """Cycle s0 -> s1 -> ... -> sN-1 -> s0."""
    states = [f"s{i}" for i in range(num_states)]
    action = "AC" * num_agents if num_agents == 2 else "AC"
    transitions = []
    unknown_transitions = []
    for i in range(num_states):
        row = ["0"] * num_states
        row[(i + 1) % num_states] = action
        transitions.append(" ".join(row))
        unknown_transitions.append(" ".join(["0"] * num_states))
    labelling = ["1"] * num_states
    return f"""Transition
{chr(10).join(transitions)}
Unknown_Transition_by
{chr(10).join(unknown_transitions)}
Name_State
{' '.join(states)}
Initial_State
s0
Atomic_propositions
{prop_name}
Labelling
{chr(10).join(labelling)}
Number_of_agents
{num_agents}
"""


def generate_cost_cgs_linear_chain_content(num_states, num_agents=2, prop_names=None):
    """Linear chain costCGS with costs for actions."""
    if prop_names is None:
        prop_names = ["p"]
    states = [f"s{i}" for i in range(num_states)]
    action = "AC" * num_agents if num_agents == 2 else "AC"
    cost_str = ":".join(["1"] * num_agents)
    transitions = []
    unknown_transitions = []
    for i in range(num_states):
        row = ["0"] * num_states
        row[i] = "*" if i == num_states - 1 else "0"
        if i + 1 < num_states:
            row[i + 1] = action
        transitions.append(" ".join(row))
        unknown_transitions.append(" ".join(["0"] * num_states))
    labelling = [["0"] * len(prop_names) for _ in range(num_states)]
    labelling[0][0] = "1"
    labelling[-1][0] = "1"
    action_costs = {}
    for i in range(num_states - 1):
        action_costs.setdefault(action, []).append(f"s{i}${cost_str}")
    action_costs.setdefault("*", []).append(f"s{num_states - 1}${cost_str}")
    costs_lines = [f"{a} {';'.join(cl)}" for a, cl in action_costs.items()]
    return f"""Transition
{chr(10).join(transitions)}
Unknown_Transition_by
{chr(10).join(unknown_transitions)}
Name_State
{' '.join(states)}
Initial_State
s0
Costs_for_actions
{chr(10).join(costs_lines)}
Atomic_propositions
{' '.join(prop_names)}
Labelling
{chr(10).join([' '.join(r) for r in labelling])}
Number_of_agents
{num_agents}
"""


__all__ = [
    "load_test_model",
    "load_cgs_from_content",
    "load_costcgs_from_content",
    "extract_states_from_result",
    "build_cgs_model_content",
    "generate_linear_chain",
    "generate_cycle_model",
    "generate_cost_cgs_linear_chain_content",
    "assert_parse_structure",
]
