"""
Tree building utilities for NatATL Recall model checker.

This module provides functions for constructing execution trees from CGS models,
converting pruned trees back to transition matrices, and building a CGS instance
from tree data for in-memory CTL verification.
"""

from typing import Dict, List

import numpy as np

from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.parsers.game_structures.cgs import CGS


def build_tree_from_CGS(cgs: CGS, model_states: List[str], height: int) -> Node:
    """Build execution tree from CGS transition matrix."""
    nodes: Dict[str, Node] = {}

    def add_children(node: Node, current_level: int) -> None:
        if current_level >= height:
            return

        state_index = cgs.get_index_by_state_name(node.state)
        transitions = cgs.transition_matrix[state_index]
        model_states = cgs.get_states()

        for next_state_index, actions in enumerate(transitions):
            if actions == 0:
                continue

            next_state = str(model_states[next_state_index])
            for action in actions.split(","):
                if next_state not in nodes:
                    nodes[next_state] = Node(next_state, cgs)

                new_child = Node(
                    next_state,
                    cgs,
                    action=action,
                    predecessors=node.predecessors + [node.state],
                )
                node.add_child(new_child, action=action)
                nodes[f"{node.state}_{action}_{next_state}"] = new_child

                add_children(new_child, current_level + 1)

    initial_state = cgs.get_initial_state()
    root = Node(initial_state, cgs)
    nodes[initial_state] = root

    add_children(root, 1)

    return root


def tree_to_initial_CGS(
    root: Node,
    states: List[str],
    num_agents: int,
    max_depth: int,
) -> List[List[str]]:
    """
    Convert pruned tree back to transition matrix for CTL verification.

    After pruning, the tree represents the restricted model. This function
    converts it back to a transition matrix format that CTL model checking
    can process.

    Args:
        root: Root node of the pruned tree
        states: List of state names in the tree
        num_agents: Number of agents in the model
        max_depth: Maximum traversal depth

    Returns:
        Transition matrix as list of lists
    """
    state_index = {state: idx for idx, state in enumerate(states)}

    transition_matrix = [
        ["0" for _ in range(len(state_index))] for _ in range(len(state_index))
    ]

    def traverse(node: Node, depth: int) -> None:
        if depth > max_depth or not node:
            return
        state_idx = state_index[node.state]
        for child, actions in zip(node.children, node.actions):
            child_idx = state_index[child.state]
            action_value = str(actions)
            existing_value = transition_matrix[state_idx][child_idx]
            if existing_value == "0":
                transition_matrix[state_idx][child_idx] = action_value
            elif existing_value != action_value:
                transition_matrix[state_idx][
                    child_idx
                ] = f"{existing_value},{action_value}"
            traverse(child, depth + 1)

    traverse(root, 0)
    return transition_matrix


def _collect_labels_dfs(node: Node, out: List) -> None:
    """Append label_row for each node in DFS order (same as get_states_from_tree)."""
    out.append(node.label_row)
    for child in node.children:
        _collect_labels_dfs(child, out)


def build_cgs_from_tree(
    cgs: CGS,
    tree: Node,
    tree_states: List[str],
    unwinded_CGS: List[List],
) -> CGS:
    """
    Build a CGS instance from pruned tree data for in-memory CTL verification.

    Args:
        cgs: Original CGS (provides agents, propositions, actions)
        tree: Root of pruned tree (after rename_nodes)
        tree_states: State names in tree (same order as get_states_from_tree)
        unwinded_CGS: Transition matrix from tree_to_initial_CGS

    Returns:
        New CGS instance with pruned graph, states, and labelling
    """
    pruned = CGS()
    pruned.graph = [row[:] for row in unwinded_CGS]
    pruned.states = np.array(tree_states)
    pruned.initial_state = (
        cgs.initial_state
        if cgs.initial_state in tree_states
        else (tree_states[0] if tree_states else "")
    )
    pruned.number_of_agents = cgs.number_of_agents
    pruned.actions = cgs.actions[:] if cgs.actions else []
    pruned.atomic_propositions = (
        cgs.atomic_propositions.copy()
        if hasattr(cgs.atomic_propositions, "copy")
        else list(cgs.atomic_propositions)
    )
    labelling = []
    _collect_labels_dfs(tree, labelling)
    pruned.matrix_prop = [row[:] if row else [] for row in labelling]
    return pruned
