"""CGS model structure validation.

Checks states, agents, transition matrix, labelling matrix, and NatATL/tree rules.
"""

from typing import List

from . import cgs_actions


def get_num_states(states) -> int:
    """Return how many states there are; 0 if the list/array is empty."""
    return len(states) if hasattr(states, "__len__") and len(states) > 0 else 0


def validate_transition_matrix_dimensions(
    graph: List[List], num_states: int
) -> List[str]:
    """Check that the transition matrix has the right shape for the given number of states.

    Returns a list of error messages; empty if everything is fine.
    """
    errors = []
    if not graph:
        errors.append("Transition matrix is missing or empty")
        return errors

    if num_states > 0:
        if len(graph) != num_states:
            errors.append(
                f"Transition matrix has {len(graph)} rows but model has {num_states} states. "
                "Transition matrix rows must match the number of states."
            )
        # Check each row has correct number of columns
        if graph:
            expected_cols = len(graph[0])
            # Find first row with incorrect column count
            for i, row in enumerate(graph):
                if len(row) != expected_cols:
                    errors.append(
                        f"Transition matrix row {i} has {len(row)} columns but "
                        f"expected {expected_cols}. All rows must have same columns."
                    )
                    break
            if expected_cols != num_states:
                errors.append(
                    f"Transition matrix has {expected_cols} columns but model has "
                    f"{num_states} states. Columns must match the number of states."
                )
    return errors


def validate_labelling_matrix_dimensions(
    matrix_prop: List[List], num_states: int, num_props: int, states
) -> List[str]:
    """Check that the labelling matrix has one row per state and one column per proposition.

    Returns a list of error messages; empty if valid. Uses states only for clearer error text.
    """
    errors = []
    if not matrix_prop:
        return errors

    if num_states > 0 and num_props > 0:
        if len(matrix_prop) != num_states:
            errors.append(
                f"Labelling matrix has {len(matrix_prop)} rows but model has {num_states} states. "
                "Labelling matrix rows must match the number of states."
            )
        # Check each row has correct number of columns
        for i, row in enumerate(matrix_prop):
            if len(row) != num_props:
                state_name = (
                    states[i]
                    if hasattr(states, "__len__") and i < len(states)
                    else "unknown"
                )
                errors.append(
                    f"Labelling matrix row {i} (state '{state_name}') "
                    f"has {len(row)} columns but model has {num_props} atomic propositions. "
                    "Labelling matrix columns must match the number of atomic propositions."
                )
                break
    return errors


def validate_nat_idle_requirements(graph: List[List], n_agents: int) -> None:
    """Check that every row has at least one idle joint action for each agent position.

    Required for NatATL. A row is valid if there exists at least one joint action in that row
    where each agent's token is an idle token ("I" or "IDLE"). Raises ValueError if a row is
    all zeros/empty or if some agent position has no idle-capable joint action.
    """
    for i, row in enumerate(graph):
        if all(elem == 0 or elem == "" for elem in row):
            raise ValueError(f"All elements in row {i} are 0")

        idle_counts = [0] * n_agents

        for elem in row:
            if elem == 0 or elem == "" or elem == "*":
                continue

            joint_actions = cgs_actions.parse_joint_action_cell(str(elem), n_agents)
            for joint in joint_actions:
                for agent_idx in range(n_agents):
                    token = joint[agent_idx]
                    if token == cgs_actions.CANONICAL_IDLE_TOKEN:
                        idle_counts[agent_idx] += 1

        if any(count == 0 for count in idle_counts):
            missing_agents = [
                idx + 1 for idx, count in enumerate(idle_counts) if count == 0
            ]
            raise ValueError(
                f"Idle error in row {i}: There has to be at least one idle "
                f"joint action for agents {missing_agents}"
            )


def collect_model_structure_errors(cgs) -> List[str]:
    """Run all structure checks on a CGS instance and return a list of error messages.

    Covers states, number of agents, initial state, transition matrix, and labelling.
    Empty list means the model structure is valid.
    """
    errors = []

    if not hasattr(cgs, "states") or len(cgs.states) == 0:
        errors.append(
            "Model must have at least one state (Name_State section is missing or empty)"
        )

    try:
        num_agents = cgs.get_number_of_agents()
        if num_agents <= 0:
            errors.append("Number_of_agents must be greater than 0")
    except ValueError as e:
        errors.append(str(e))

    if hasattr(cgs, "initial_state") and cgs.initial_state:
        if hasattr(cgs, "states") and len(cgs.states) > 0:
            if cgs.initial_state not in cgs.states:
                errors.append(
                    f"Initial state '{cgs.initial_state}' not found in state list"
                )
        else:
            errors.append("Cannot validate initial state: no states defined")
    else:
        errors.append("Initial_State section is missing or empty")

    num_states = get_num_states(cgs.states)
    errors.extend(validate_transition_matrix_dimensions(cgs.graph, num_states))

    num_props = (
        len(cgs.atomic_propositions)
        if hasattr(cgs, "atomic_propositions") and len(cgs.atomic_propositions) > 0
        else 0
    )
    errors.extend(
        validate_labelling_matrix_dimensions(
            cgs.matrix_prop, num_states, num_props, cgs.states
        )
    )

    return errors


def validate_recall_structure(graph: List[List], n_agents: int) -> None:
    """Check Recall semantics: idle rules, s0 has at least one transition, and connectivity from s0 (no forest)."""
    validate_nat_idle_requirements(graph, n_agents)

    if not any(elem != 0 and elem != "" for elem in graph[0]):
        raise ValueError(
            "Transition error: The initial state 's0' must have at least one non-zero transition"
        )

    s0_transitions_to_others = any(
        graph[0][j] != 0 and graph[0][j] != "" for j in range(1, len(graph[0]))
    )
    if not s0_transitions_to_others:
        for i in range(1, len(graph)):
            if any(elem != 0 and elem != "" for elem in graph[i]):
                raise ValueError(
                    f"Configuration error: State 's0' has no transitions to other "
                    f"states but state 's{i}' has transitions."
                )
