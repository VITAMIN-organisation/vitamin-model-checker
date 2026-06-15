"""Synthetic CGS-family model file content for tests and external tooling."""

from __future__ import annotations


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
    """Assemble model file string for CGS, costCGS, or capCGS structures."""
    if prop_names is None:
        prop_names = ["p"]
    transition_lines = [" ".join(row) for row in transitions]
    labelling_lines = [
        " ".join(row) if isinstance(row, list) else str(row) for row in labelling
    ]
    content_parts = ["Transition", "\n".join(transition_lines)]
    if unknown_transitions is not None:
        unknown_lines = [" ".join(row) for row in unknown_transitions]
        content_parts.extend(["Unknown_Transition_by", "\n".join(unknown_lines)])
    content_parts.extend(
        [
            "Name_State",
            " ".join(state_names),
            "Initial_State",
            initial_state,
        ]
    )
    if costs_for_actions is not None:
        if isinstance(costs_for_actions, str):
            costs_block = costs_for_actions
        else:
            costs_block = "\n".join(
                (
                    f"{action} {';'.join(cost_list)}"
                    if isinstance(cost_list, list)
                    else f"{action} {cost_list}"
                )
                for action, cost_list in costs_for_actions.items()
            )
        content_parts.extend(["Costs_for_actions", costs_block])
    content_parts.extend(
        [
            "Atomic_propositions",
            " ".join(prop_names),
            "Labelling",
            "\n".join(labelling_lines),
        ]
    )
    if capacities is not None:
        content_parts.extend(["Capacities", " ".join(capacities)])
    if capacities_assignment is not None:
        capacity_lines = [
            " ".join(row) if isinstance(row, list) else str(row)
            for row in capacities_assignment
        ]
        content_parts.extend(["Capacities_assignment", "\n".join(capacity_lines)])
    if actions_for_capacities is not None:
        action_capacity_lines = [
            f"{cap} {' '.join(acts)}" for cap, acts in actions_for_capacities.items()
        ]
        content_parts.extend(
            ["Actions_for_capacities", "\n".join(action_capacity_lines)]
        )
    content_parts.extend(["Number_of_agents", str(num_agents)])
    return "\n".join(content_parts) + "\n"


def _build_transition_rows(num_states: int, cell_at) -> list[str]:
    transitions = []
    for i in range(num_states):
        row = [cell_at(i, j) for j in range(num_states)]
        transitions.append(" ".join(row))
    return transitions


def _labelling_p_first_last(num_states: int, prop_names: list[str]) -> list[str]:
    rows = []
    for i in range(num_states):
        row = []
        for prop in prop_names:
            if prop == "p":
                row.append("1" if (i == 0 or i == num_states - 1) else "0")
            else:
                row.append("0")
        rows.append(" ".join(row))
    return rows


def generate_linear_chain(
    num_states,
    num_agents=2,
    prop_names=None,
    dense_p=False,
    action_label="1",
):
    """Linear chain s0 -> s1 -> ... -> sN-1.

    action_label: "1" for simple numeric transitions; "AC" for CGS action strings.
    dense_p: when True, p on all but last state.
    """
    if prop_names is None:
        prop_names = ["p"]
    state_names = [f"s{i}" for i in range(num_states)]
    use_ac = action_label == "AC"
    action = "AC" * num_agents if use_ac else "1"
    transitions = []
    unknown_transitions = [] if use_ac else None
    for i in range(num_states):
        row = ["0"] * num_states
        if i == num_states - 1:
            row[i] = "*" if use_ac else "1"
        elif i + 1 < num_states:
            row[i + 1] = action
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
    unknown_transitions = [" ".join(["0"] * num_states)] * num_states
    forward_action = "AC" * num_agents

    def cell_at(i, j):
        if j == (i + 1) % num_states:
            return forward_action
        return "0"

    transitions = _build_transition_rows(num_states, cell_at)
    labelling = ["1"] * num_states
    return build_cgs_model_content(
        transitions=[row.split() for row in transitions],
        state_names=states,
        initial_state="s0",
        prop_names=[prop_name],
        labelling=labelling,
        num_agents=num_agents,
        unknown_transitions=[row.split() for row in unknown_transitions],
    )


def generate_natatl_linear_chain_model(num_states, num_agents=2, prop_names=None):
    """Linear chain with NatATL-style idle/forward actions."""
    if prop_names is None:
        prop_names = ["p"]

    states = [f"s{i}" for i in range(num_states)]
    unknown_transitions = [" ".join(["0"] * num_states)] * num_states
    idle_action = "I" * num_agents if num_agents > 1 else "I"
    forward_action = "C" * num_agents if num_agents > 1 else "C"

    def cell_at(i, j):
        if j == i:
            return idle_action
        if j == i + 1:
            return forward_action
        return "0"

    transitions = _build_transition_rows(num_states, cell_at)
    labelling = _labelling_p_first_last(num_states, prop_names)
    return build_cgs_model_content(
        transitions=[row.split() for row in transitions],
        state_names=states,
        initial_state="s0",
        prop_names=prop_names,
        labelling=labelling,
        num_agents=num_agents,
        unknown_transitions=[row.split() for row in unknown_transitions],
    )


def generate_capcgs_linear_chain_model(num_states, num_agents=2, prop_names=None):
    """Linear capCGS chain with capacity metadata."""
    if prop_names is None:
        prop_names = ["p"]

    states = [f"s{i}" for i in range(num_states)]
    unknown_transitions = [" ".join(["0"] * num_states)] * num_states
    forward_action = "A" + "*" * (num_agents - 1)
    terminal_action = "*" * num_agents

    def cell_at(i, j):
        if j == i + 1:
            return forward_action
        if j == i and i == num_states - 1:
            return terminal_action
        return "0"

    transitions = _build_transition_rows(num_states, cell_at)
    labelling = _labelling_p_first_last(num_states, prop_names)
    return build_cgs_model_content(
        transitions=[row.split() for row in transitions],
        state_names=states,
        initial_state="s0",
        prop_names=prop_names,
        labelling=labelling,
        num_agents=num_agents,
        unknown_transitions=[row.split() for row in unknown_transitions],
        capacities=["c"],
        capacities_assignment=[["1"] for _ in range(num_agents)],
        actions_for_capacities={"c": ["A"]},
    )


def generate_cost_cgs_linear_chain_content(num_states, num_agents=2, prop_names=None):
    """Linear costCGS chain with per-action costs."""
    if prop_names is None:
        prop_names = ["p"]

    states = [f"s{i}" for i in range(num_states)]
    unknown_transitions = [" ".join(["0"] * num_states)] * num_states
    forward_action = "AC" * num_agents

    def cell_at(i, j):
        if j == i + 1:
            return forward_action
        if j == i:
            return "*" if i == num_states - 1 else "0"
        return "0"

    transitions = _build_transition_rows(num_states, cell_at)
    labelling = [["0"] * len(prop_names) for _ in range(num_states)]
    labelling[0][0] = "1"
    labelling[-1][0] = "1"
    labelling_str = [" ".join(row) for row in labelling]

    cost_str = ":".join(["1"] * num_agents)
    action_costs = {}
    for i in range(num_states - 1):
        action_costs.setdefault(forward_action, []).append(f"s{i}${cost_str}")
    action_costs["*"] = [f"s{num_states - 1}${cost_str}"]
    costs_lines = "\n".join(
        f"{action} {';'.join(cost_list)}" for action, cost_list in action_costs.items()
    )

    return build_cgs_model_content(
        transitions=[row.split() for row in transitions],
        state_names=states,
        initial_state="s0",
        prop_names=prop_names,
        labelling=labelling_str,
        num_agents=num_agents,
        unknown_transitions=[row.split() for row in unknown_transitions],
        costs_for_actions=costs_lines,
    )


__all__ = [
    "build_cgs_model_content",
    "generate_linear_chain",
    "generate_cycle_model",
    "generate_natatl_linear_chain_model",
    "generate_capcgs_linear_chain_model",
    "generate_cost_cgs_linear_chain_content",
]
