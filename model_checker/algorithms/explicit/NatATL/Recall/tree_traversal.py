"""Tree pruning, depth-first search, and regex pattern matching for NatATL Recall execution trees."""

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
    valid_actions: dict[str, list[str]],
    input_nodes: list[str],
    index: int,
    path: list[str],
    height: int,
    current_depth: int = 0,
    visited: set[int] | None = None,
) -> None:
    """
    Drop child edges whose agent action is not allowed at nodes on ``path``.

    ``visited`` tracks node ids so shared subtrees are not pruned twice.
    """
    if visited is None:
        visited = set()

    if path:
        if node is None or id(node) in visited or current_depth >= len(path):
            return

    visited.add(id(node))

    if node.state in input_nodes and node.state == path[current_depth]:
        to_remove = []
        for i, (child, actions) in enumerate(
            zip(node.children, node.actions, strict=False)
        ):
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
) -> list[str] | None:
    """Enumerate regex witnesses and return the first path that matches the tree."""
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
    word: list[str],
    predecessors: list[str],
    depth: int,
    max_depth: int,
) -> list[str] | None:
    """DFS check that ``word`` labels a path from ``node``; return the path or None."""
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
