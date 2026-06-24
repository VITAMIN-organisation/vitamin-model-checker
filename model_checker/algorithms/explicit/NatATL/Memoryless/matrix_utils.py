"""Transition matrix updates for NatATL memoryless strategy pruning."""

import logging

logger = logging.getLogger(__name__)


def modify_matrix(
    graph: list[list],
    label_matrix: list[list[str]],
    states: set[str],
    action: str,
    agent_index: int,
    agents: list[int],
) -> list[list]:
    """Keep only transitions where one agent plays action in the given states."""
    new_graph = [row.copy() for row in graph]

    # agents[agent_index-1] gives the actual agent number
    # We subtract 1 again for the 0-based index in the per-agent token list
    tuple_idx = agents[agent_index - 1] - 1

    # Normalize the required action token (align with canonical idle tokens)
    from model_checker.parsers.game_structures.cgs.cgs_actions import (
        AGENT_ACTION_SEPARATOR,
        CANONICAL_IDLE_TOKEN,
        JOINT_CHOICE_SEPARATOR,
        normalize_action_token,
    )

    required_token = normalize_action_token(action)

    for i, row in enumerate(new_graph):
        for j, elem in enumerate(row):
            if label_matrix[i][j] in states:
                if isinstance(elem, str) and elem != "*":
                    elem_parts = elem.split(JOINT_CHOICE_SEPARATOR)
                    new_elem_parts = []
                    for part in elem_parts:
                        # part encodes a joint action with per-agent tokens
                        tokens = [
                            normalize_action_token(t)
                            for t in part.split(AGENT_ACTION_SEPARATOR)
                            if t != ""
                        ]
                        if tuple_idx < len(tokens):
                            agent_token = tokens[tuple_idx]
                            if (
                                agent_token == CANONICAL_IDLE_TOKEN
                                or agent_token == required_token
                            ):
                                new_elem_parts.append(part)

                    new_elem = JOINT_CHOICE_SEPARATOR.join(new_elem_parts)
                    if new_elem:
                        new_graph[i][j] = new_elem
                    else:
                        new_graph[i][j] = 0
    return new_graph
