"""
Tree traversal and path matching for NatATL Recall model checker.

This module provides functions for tree pruning, depth-first search,
and regex pattern matching on execution tree paths.
"""

from typing import Dict, List, Optional, Set

from model_checker.algorithms.explicit.NatATL.Recall.regex_parser import (
    check_prop_holds_in_label_row,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.algorithms.explicit.NatATL.Recall.witness_parser import (
    RegexWitnessGenerator,
    store_word,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol


def prune_tree(
    node: Node,
    valid_actions: Dict[str, List[str]],
    input_nodes: List[str],
    index: int,
    path: List[str],
    height: int,
    current_depth: int = 0,
    visited: Optional[Set[int]] = None,
) -> None:
    """
    Prune tree to only allow valid actions at specified nodes.

    For nodes matching the input_nodes list and current path position,
    removes children whose edge action doesn't match valid_actions.

    Args:
        node: Current node being processed
        valid_actions: Dict mapping agent keys to allowed action lists
        input_nodes: List of node names to consider for pruning
        index: Agent index for action lookup
        path: Expected path sequence for validation
        height: Maximum tree height
        current_depth: Current recursion depth
        visited: Set of visited node ids (for cycle detection; avoids pruning distinct branches that revisit the same state)
    """
    if visited is None:
        visited = set()

    if path:
        if node is None or id(node) in visited or current_depth >= len(path):
            return

    visited.add(id(node))

    if node.state in input_nodes and node.state == path[current_depth]:
        to_remove = []
        for i, (child, actions) in enumerate(zip(node.children, node.actions)):
            updated_actions = []
            for action in actions:
                valid_action_found = False
                agent_key = f"agent{index}"

                if agent_key in action:
                    act = action[agent_key]
                    if (
                        agent_key in valid_actions and act in valid_actions[agent_key]
                    ) or act == "I":
                        valid_action_found = True
                    else:
                        valid_action_found = False
                        break

                if valid_action_found:
                    updated_actions.append(action)

            if not updated_actions:
                to_remove.append((i, child))
            else:
                node.actions[i] = updated_actions

        for i, _child in reversed(to_remove):
            del node.children[i]
            del node.actions[i]

    for child in node.children:
        prune_tree(
            child,
            valid_actions,
            input_nodes,
            index,
            path,
            height,
            current_depth + 1,
            visited,
        )


def depth_first_search(
    cgs: CGSProtocol,
    node: Node,
    pattern: str,
    length: int,
    max_depth: int = 2,
) -> Optional[List[str]]:
    """
    Find a path in the tree matching a regex pattern.

    Uses regex witness generation to enumerate possible matching words,
    then verifies each against the tree structure.

    Args:
        cgs: CGS model object
        node: Root node to search from
        pattern: Regex pattern to match
        length: Expected witness length
        max_depth: Maximum search depth

    Returns:
        List of state names forming a matching path, or None if no match
    """
    generator = RegexWitnessGenerator(pattern, length)
    word = generator.next_word()

    while word is not None:
        stored_word = store_word(word)
        result = dfs_verify_word(cgs, node, stored_word, [], 0, max_depth)
        if result is not None:
            return result
        word = generator.next_word()
    return None


def dfs_verify_word(
    cgs: CGSProtocol,
    node: Node,
    word: List[str],
    predecessors: List[str],
    depth: int,
    max_depth: int,
) -> Optional[List[str]]:
    """
    Verify if a word (sequence of propositions) matches a tree path.

    Args:
        cgs: CGS model object
        node: Current node in DFS
        word: Sequence of proposition conditions to match
        predecessors: Path of states visited so far
        depth: Current position in word
        max_depth: Maximum search depth

    Returns:
        Complete path if word matches, None otherwise
    """
    if depth == len(word):
        return predecessors

    if depth > max_depth:
        return None

    current_predecessors = predecessors + [node.state]
    if check_prop_holds_in_label_row(cgs, word[depth], node.label_row):
        if depth == len(word) - 1:
            return current_predecessors
        for child in node.children:
            result = dfs_verify_word(
                cgs, child, word, current_predecessors, depth + 1, max_depth
            )
            if result is not None:
                return result
    return None
