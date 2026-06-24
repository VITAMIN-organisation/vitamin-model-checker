"""Build recall execution trees and flatten pruned trees for CTL."""

import numpy as np

from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.parsers.game_structures.cgs import CGS


def build_tree_from_CGS(cgs: CGS, model_states: list[str], height: int) -> Node:
    """Build execution tree from CGS transition matrix."""
    nodes: dict[str, Node] = {}

    def add_children(node: Node, current_level: int) -> None:
        if current_level >= height:
            return

        state_index = cgs.get_index_by_state_name(node.state)
        transitions = cgs.graph[state_index]
        model_states = cgs.states

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

    initial_state = cgs.initial_state
    root = Node(initial_state, cgs)
    nodes[initial_state] = root

    add_children(root, 1)

    return root


def tree_to_initial_CGS(
    root: Node,
    states: list[str],
    max_depth: int,
) -> list[list[str]]:
    """Pruned tree to transition matrix (for CTL on the restricted model)."""
    state_index = {state: idx for idx, state in enumerate(states)}

    transition_matrix = [
        ["0" for _ in range(len(state_index))] for _ in range(len(state_index))
    ]

    def traverse(node: Node, depth: int) -> None:
        if depth > max_depth or not node:
            return
        state_idx = state_index[node.state]
        for child, actions in zip(node.children, node.actions, strict=False):
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


def build_cgs_from_tree(
    cgs: CGS,
    tree: Node,
    tree_states: list[str],
    unwinded_CGS: list[list],
) -> CGS:
    """CGS copy with graph and labelling taken from the pruned tree."""
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

    def collect_labels(node: Node) -> None:
        labelling.append(node.label_row)
        for child in node.children:
            collect_labels(child)

    collect_labels(tree)
    pruned.matrix_prop = [row[:] if row else [] for row in labelling]
    return pruned
