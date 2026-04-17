"""Standalone model content generators for benchmarks."""

NL = "\n"


def _state_names(num_states):
    return [f"s{i}" for i in range(num_states)]


def _unknown_transitions_grid(num_states):
    row = " ".join(["0"] * num_states)
    return [row] * num_states


def _format_cgs_body(
    transitions,
    unknown_transitions,
    states,
    atomic_propositions,
    labelling,
    num_agents,
    costs_for_actions=None,
    extra_after_labelling=None,
):
    parts = [
        "Transition",
        NL.join(transitions),
        "Unknown_Transition_by",
        NL.join(unknown_transitions),
        "Name_State",
        " ".join(states),
        "Initial_State",
        "s0",
    ]
    if costs_for_actions is not None:
        parts.append("Costs_for_actions")
        parts.append(costs_for_actions)
    parts.extend(
        [
            "Atomic_propositions",
            atomic_propositions,
            "Labelling",
            NL.join(labelling),
        ]
    )
    if extra_after_labelling:
        parts.append(extra_after_labelling)
    parts.extend(["Number_of_agents", str(num_agents)])
    return NL.join(parts) + NL


def _labelling_p_first_last(num_states, prop_names):
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


def generate_linear_chain_model(
    num_states, num_agents=2, prop_names=None, dense_p=False
):
    if prop_names is None:
        prop_names = ["p"]

    states = _state_names(num_states)
    transitions = []
    unknown_transitions = _unknown_transitions_grid(num_states)

    for i in range(num_states):
        row = []
        for j in range(num_states):
            if j == i + 1:
                action = "AC" * num_agents
                row.append(action)
            elif j == i:
                row.append("*" if (i == num_states - 1) else "0")
            else:
                row.append("0")
        transitions.append(" ".join(row))

    labelling = []
    for i in range(num_states):
        row = []
        for prop in prop_names:
            if prop == "p":
                if dense_p:
                    row.append("1" if i < num_states - 1 else "0")
                else:
                    row.append("1" if (i == 0 or i == num_states - 1) else "0")
            elif prop == "q":
                row.append("1" if i == num_states - 1 else "0")
            else:
                row.append("0")
        labelling.append(" ".join(row))

    return _format_cgs_body(
        transitions,
        unknown_transitions,
        states,
        " ".join(prop_names),
        labelling,
        num_agents,
    )


def generate_cycle_model(num_states, num_agents=2, prop_name="p"):
    states = _state_names(num_states)
    transitions = []
    unknown_transitions = _unknown_transitions_grid(num_states)

    for i in range(num_states):
        row = []
        for j in range(num_states):
            if j == (i + 1) % num_states:
                action = "AC" * num_agents
                row.append(action)
            else:
                row.append("0")
        transitions.append(" ".join(row))

    labelling = ["1"] * num_states
    return _format_cgs_body(
        transitions, unknown_transitions, states, prop_name, labelling, num_agents
    )


def generate_natatl_linear_chain_model(num_states, num_agents=2, prop_names=None):
    if prop_names is None:
        prop_names = ["p"]

    states = _state_names(num_states)
    transitions = []
    unknown_transitions = _unknown_transitions_grid(num_states)

    for i in range(num_states):
        row = []
        for j in range(num_states):
            if j == i:
                idle_action = "I" * num_agents if num_agents > 1 else "I"
                row.append(idle_action)
            elif j == i + 1:
                action = "C" * num_agents if num_agents > 1 else "C"
                row.append(action)
            else:
                row.append("0")
        transitions.append(" ".join(row))

    labelling = _labelling_p_first_last(num_states, prop_names)
    return _format_cgs_body(
        transitions,
        unknown_transitions,
        states,
        " ".join(prop_names),
        labelling,
        num_agents,
    )


def generate_capcgs_linear_chain_model(num_states, num_agents=2, prop_names=None):
    if prop_names is None:
        prop_names = ["p"]

    states = _state_names(num_states)
    transitions = []
    unknown_transitions = _unknown_transitions_grid(num_states)

    for i in range(num_states):
        row = []
        for j in range(num_states):
            if j == i + 1:
                action = "A" + "*" * (num_agents - 1)
                row.append(action)
            elif j == i and i == num_states - 1:
                row.append("*" * num_agents)
            else:
                row.append("0")
        transitions.append(" ".join(row))

    labelling = _labelling_p_first_last(num_states, prop_names)
    extra = NL.join(
        [
            "Capacities",
            "c",
            "Capacities_assignment",
            NL.join(["1"] * num_agents),
            "Actions_for_capacities",
            "c A",
        ]
    )
    return _format_cgs_body(
        transitions,
        unknown_transitions,
        states,
        " ".join(prop_names),
        labelling,
        num_agents,
        extra_after_labelling=extra,
    )


def generate_cost_cgs_linear_chain_content(num_states, num_agents=2, prop_names=None):
    if prop_names is None:
        prop_names = ["p"]

    states = _state_names(num_states)
    transitions = []
    unknown_transitions = _unknown_transitions_grid(num_states)

    for i in range(num_states):
        row = []
        for j in range(num_states):
            if j == i + 1:
                action = "AC" * num_agents
                row.append(action)
            elif j == i:
                row.append("*" if i == num_states - 1 else "0")
            else:
                row.append("0")
        transitions.append(" ".join(row))

    labelling = [["0"] * len(prop_names) for _ in range(num_states)]
    labelling[0][0] = "1"
    labelling[-1][0] = "1"
    labelling_str = [" ".join(row) for row in labelling]

    base_action = "AC" * num_agents
    cost_str = ":".join(["1"] * num_agents)
    action_costs = {}
    for i in range(num_states - 1):
        state_name = f"s{i}"
        if base_action not in action_costs:
            action_costs[base_action] = []
        action_costs[base_action].append(f"{state_name}${cost_str}")
    action_costs["*"] = [f"s{num_states - 1}${cost_str}"]
    costs_lines = NL.join(
        [
            f"{action} {';'.join(cost_list)}"
            for action, cost_list in action_costs.items()
        ]
    )

    return _format_cgs_body(
        transitions,
        unknown_transitions,
        states,
        " ".join(prop_names),
        labelling_str,
        num_agents,
        costs_for_actions=costs_lines,
    )
