"""
Regex pruning for NatATL Recall model checker.

This module implements pruning based on regex patterns that match execution
history paths in the tree.
"""

import logging
from typing import List

from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.algorithms.explicit.NatATL.Recall.tree_traversal import (
    depth_first_search,
)
from model_checker.parsers.game_structures.cgs.cgs import CGS

logger = logging.getLogger(__name__)


def regex_pruning(
    cgs: CGS,
    tree: Node,
    condition: str,
    action: str,
    strategy_index: int,
    height: int,
) -> int:
    """
    Prune tree based on regex pattern matching on paths.
    """
    path = depth_first_search(cgs, tree, condition, height, height)
    if path is None:
        logger.debug("No path matches regex condition: %s", condition)
        return 0

    logger.debug("Path matching regex condition: %s", path)

    def prune_nodes_along_path(
        node: Node,
        path: List[str],
        action: str,
        strategy_index: int,
        current_level: int,
    ) -> int:
        """Prune only nodes along the matched regex path."""
        pruning_occurred = 0

        if current_level < len(path) and node.state == path[current_level]:
            children_to_remove = []
            for i, (_child, actions) in enumerate(zip(node.children, node.actions)):
                if strategy_index - 1 < len(actions):
                    if (actions[strategy_index - 1] != action) and (not node.pruned):
                        children_to_remove.append(i)
                        pruning_occurred = 1

            if pruning_occurred == 1:
                node.pruned = True

            for i in reversed(children_to_remove):
                del node.children[i]
                del node.actions[i]

            for child in node.children:
                if prune_nodes_along_path(
                    child, path, action, strategy_index, current_level + 1
                ):
                    pruning_occurred = 1

        return pruning_occurred

    return prune_nodes_along_path(tree, path, action, strategy_index, 0)
