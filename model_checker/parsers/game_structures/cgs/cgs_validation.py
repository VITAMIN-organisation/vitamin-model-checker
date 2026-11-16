"""CGS model structure validation.

Checks states, agents, transition matrix, labelling matrix, and NatATL/tree rules.
"""

import itertools
import math
from collections.abc import Collection

from . import cgs_actions

_EMPTY_TRANSITION_CELLS = frozenset({0, "", "0", None})


def validate_transition_matrix_dimensions(
    graph: list[list], num_states: int
) -> list[str]:
    """Check that the transition matrix has the right shape for the given number of states.

    Returns a list of error messages; empty if everything is fine.
    """
    errors = []
    if len(graph) == 0:
        errors.append("Transition matrix is missing or empty")
        return errors

    if num_states > 0:
        if len(graph) != num_states:
            errors.append(
                f"Transition matrix has {len(graph)} rows but model has {num_states} states. "
                "Transition matrix rows must match the number of states."
            )
        # Check each row has correct number of columns
        if len(graph) > 0:
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
    matrix_prop: list[list], num_states: int, props: Collection[str], states
) -> list[str]:
    """Check that the labelling matrix has one row per state and one column per
    proposition in `props`, and that it exists when `props` is not empty.

    Returns a list of error messages; empty if valid. Uses states only for clearer error text.
    """
    errors = []
    num_props = len(props)
    if len(matrix_prop) == 0:
        if num_props > 0:
            names = ", ".join(f"'{p}'" for p in props)
            errors.append(
                f"Labelling section is missing or empty but Atomic_propositions "
                f"declares {names}. Give one row per state with one label per proposition."
            )
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


def validate_nat_idle_requirements(graph: list[list], n_agents: int) -> None:
    """Raise ValueError unless every row has a joint action where each agent is idle
    ("I" or "IDLE"), as NatATL requires."""
    for i, row in enumerate(graph):
        if not any(elem not in _EMPTY_TRANSITION_CELLS for elem in row):
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


def validate_total_transitions(graph: list[list], states) -> list[str]:
    """Require a successor for every state, as CTL and ATL assume; a terminal state
    uses a self-loop such as ``*``."""
    errors = []
    if len(graph) == 0:
        return errors

    for i, row in enumerate(graph):
        if any(elem not in _EMPTY_TRANSITION_CELLS for elem in row):
            continue
        if hasattr(states, "__len__") and i < len(states):
            state_name = str(states[i])
        else:
            state_name = f"index {i}"
        errors.append(
            f"State '{state_name}' has no outgoing transitions. "
            "Every state must have at least one successor "
            "(use '*' for a self-loop on terminal states)."
        )
    return errors


_MISSING_EXAMPLES_SHOWN = 3


def _row_joint_actions(row: list, n_agents: int) -> list[tuple[str, ...]]:
    """The joint actions of one row; a `*` cell is `*` for every agent."""
    return [
        tuple(profile.split(cgs_actions.AGENT_ACTION_SEPARATOR))
        for elem in row
        if elem not in _EMPTY_TRANSITION_CELLS
        for profile in cgs_actions.build_action_list(str(elem), n_agents)
    ]


def validate_complete_joint_actions(
    graph: list[list], states, n_agents: int
) -> list[str]:
    """One error per state that lacks a transition for some combination of the actions
    each agent plays in its row; `*` in an agent's position covers all its actions."""
    errors = []
    for i, row in enumerate(graph):
        try:
            joints = _row_joint_actions(row, n_agents)
        except ValueError:
            # A profile of the wrong length is reported by the checker that reads it.
            continue
        if not joints:
            # A row with no transition is reported by validate_total_transitions.
            continue
        available = [
            sorted({j[k] for j in joints if j[k] != "*"}) or ["*"]
            for k in range(n_agents)
        ]
        listed = set(joints)
        with_star = [j for j in listed if "*" in j]
        if not with_star and len(listed) == math.prod(len(a) for a in available):
            continue
        missing = [
            combo
            for combo in itertools.product(*available)
            if combo not in listed
            and not any(
                all(j[k] in ("*", combo[k]) for k in range(n_agents)) for j in with_star
            )
        ]
        if not missing:
            continue
        examples = ", ".join(
            cgs_actions.AGENT_ACTION_SEPARATOR.join(c)
            for c in missing[:_MISSING_EXAMPLES_SHOWN]
        )
        errors.append(
            f"State '{states[i]}' has no transition for {len(missing)} combination(s) "
            f"of available actions, such as {examples}. Every combination of the "
            "actions the agents play in a row needs a transition: add each one to "
            "the cell of the state it leads to."
        )
    return errors


def raise_structure_errors(errors: list[str]) -> None:
    """Raise one ValueError listing every structure error, if there is any."""
    if errors:
        raise ValueError(
            "Model structure validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def collect_state_errors(model) -> list[str]:
    """Check that the model has states and that its initial state is one of them."""
    errors = []
    if not hasattr(model, "states") or len(model.states) == 0:
        errors.append(
            "Model must have at least one state (Name_State section is missing or empty)"
        )

    if hasattr(model, "initial_state") and model.initial_state:
        if hasattr(model, "states") and len(model.states) > 0:
            if model.initial_state not in model.states:
                errors.append(
                    f"Initial state '{model.initial_state}' not found in state list"
                )
        else:
            errors.append("Cannot validate initial state: no states defined")
    elif model.initial_state_required:
        errors.append("Initial_State section is missing or empty")
    return errors


def collect_model_structure_errors(cgs) -> list[str]:
    """The structure errors of a CGS (states, agents, initial state, transitions,
    labelling); an empty list means it is valid."""
    errors = collect_state_errors(cgs)

    num_agents = 0
    try:
        num_agents = cgs.get_number_of_agents()
        if num_agents <= 0:
            errors.append("Number_of_agents must be greater than 0")
    except ValueError as e:
        errors.append(str(e))

    num_states = (
        len(cgs.states) if hasattr(cgs.states, "__len__") and len(cgs.states) > 0 else 0
    )
    shape_errors = validate_transition_matrix_dimensions(cgs.graph, num_states)
    errors.extend(shape_errors)
    errors.extend(validate_total_transitions(cgs.graph, cgs.states))
    # Edge-cost cells (Transition_With_Costs) hold no actions to combine.
    if (
        not shape_errors
        and num_agents > 0
        and not cgs.partial_transitions_allowed
        and not getattr(cgs, "usesCostsInsteadOfActions", False)
    ):
        errors.extend(
            validate_complete_joint_actions(cgs.graph, cgs.states, num_agents)
        )

    errors.extend(
        validate_labelling_matrix_dimensions(
            cgs.matrix_prop,
            num_states,
            cgs.atomic_propositions,
            cgs.states,
        )
    )

    agent_labels = getattr(cgs, "agent_labels", None) or []
    if agent_labels:
        try:
            num_agents = cgs.get_number_of_agents()
            if len(agent_labels) != num_agents:
                errors.append(
                    f"Agent_labels has {len(agent_labels)} label(s) but "
                    f"Number_of_agents is {num_agents}. "
                    "Provide one whitespace-separated label per agent."
                )
        except ValueError as e:
            errors.append(str(e))

    return errors
