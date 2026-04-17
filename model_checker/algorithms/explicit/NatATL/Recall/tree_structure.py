"""
Tree node structure for NatATL Recall model checker.

This module defines the Node class representing states in execution traces
and basic tree operations like renaming and state extraction.
"""

from typing import List, Optional

from model_checker.parsers.game_structures.cgs import CGS


class Node:
    """
    Tree node representing a state in an execution trace.

    Each node corresponds to a state in the CGS model and contains:
    - State identifier (name)
    - Label information (which atomic propositions hold)
    - Children with corresponding action labels
    - Predecessor path (for history-aware verification)

    Attributes:
        cgs: Reference to the CGS model
        state: State name (e.g., 's0', 's1')
        action: Action that led to this node (from parent)
        children: List of child nodes (successors)
        predecessors: List of state names on path from root
        label_row: Proposition values for this state
        actions: List of action tuples for each child edge
        old_state: Original state name (before renaming)
        pruned: Flag indicating if node has been pruned
    """

    def __init__(
        self,
        name: str,
        cgs: CGS,
        action: Optional[str] = None,
        predecessors: Optional[List[str]] = None,
    ):
        self.cgs = cgs
        self.state = str(name)
        self.action = action
        self.children: List[Node] = []
        self.predecessors = (
            [str(p) for p in predecessors] if predecessors is not None else []
        )
        self.label_row = self.get_label_row_list(
            cgs.get_states(), cgs.get_matrix_proposition()
        )
        self.actions: List[str] = []
        self.old_state = name
        self.pruned = False

    def add_child(self, child: "Node", action: Optional[str] = None) -> None:
        """Add a child node with an optional action label."""
        self.children.append(child)
        if action:
            self.actions.append(action)

    def __repr__(self, level: int = 0) -> str:
        """Return indented representation for debugging."""
        ret = "\t" * level + repr(self.state)
        if self.action:
            ret += f" ({self.action})"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    def __str__(self, level: int = 0) -> str:
        """Return detailed string representation with all attributes."""
        ret = (
            " " * level
            + f"Name: {self.state}, Original: {self.old_state}, "
            + f"Action: {self.action}, Predecessors: {self.predecessors}, "
            + f"Labels: {self.label_row}, Pruned: {self.pruned}\n"
        )
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def get_label_row_list(
        self, states: List[str], label_matrix: List[List]
    ) -> Optional[List]:
        """Get proposition values for this state from the label matrix."""
        for i, state in enumerate(states):
            if self.state == state:
                return label_matrix[i]
        return None


def rename_nodes(tree: Node) -> None:
    """
    Rename all nodes in the tree with sequential state names.

    After pruning, state names may be duplicated or inconsistent.
    This function assigns fresh sequential names (s1, s2, s3, ...)
    to all nodes except the root (which stays s0).

    Args:
        tree: Root node of the tree to rename
    """

    def rename(node: Node, counter: int) -> int:
        for child in node.children:
            child.state = f"s{counter}"
            counter += 1
            counter = rename(child, counter)
        return counter

    rename(tree, 1)


def get_states_from_tree(root: Node) -> List[str]:
    """
    Extract all unique state names from the tree.

    Args:
        root: Root node of the tree

    Returns:
        List of state names in DFS order
    """
    states: List[str] = []

    def traverse(node: Node) -> None:
        if node.state not in states:
            states.append(node.state)
        for child in node.children:
            traverse(child)

    traverse(root)
    return states


def reset_pruned_flag(node: Node) -> None:
    """
    Reset pruned flag for all nodes in the tree.

    Called between agent pruning passes to allow re-pruning.

    Args:
        node: Root node of the tree
    """
    node.pruned = False
    for child in node.children:
        reset_pruned_flag(child)


def are_all_nodes_pruned(tree: Node) -> bool:
    """
    Check if all nodes in the tree have been pruned.

    A fully pruned tree indicates that the strategy covers all states.

    Args:
        tree: Root node of the tree

    Returns:
        True if all nodes have pruned=True, False otherwise
    """
    if tree.pruned is False:
        return False
    for child in tree.children:
        if not are_all_nodes_pruned(child):
            return False
    return True
