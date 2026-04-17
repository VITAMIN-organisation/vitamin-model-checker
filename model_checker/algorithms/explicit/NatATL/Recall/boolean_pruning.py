"""
Boolean pruning for NatATL Recall model checker.

This module implements pruning based on propositional (boolean) conditions
using CTL model checking to determine which states satisfy the condition.
"""

import logging
from typing import Set

from model_checker.algorithms.explicit.NatATL.Recall.condition_cache import (
    ctl_model_checking_cached,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs.cgs import CGS

logger = logging.getLogger(__name__)


def prune_tree_nodes(
    node: Node,
    state_set: Set[str],
    action: str,
    strategy_index: int,
    current_level: int = 0,
) -> int:
    """
    Generic tree pruning: remove children where agent action doesn't match.
    """
    pruning_occurred = 0

    if node.state in state_set:
        children_to_remove = []
        for i, (_child, actions) in enumerate(zip(node.children, node.actions)):
            if strategy_index - 1 < len(actions):
                if (actions[strategy_index - 1] != action) and (not node.pruned):
                    children_to_remove.append(i)
                    pruning_occurred = 1
            else:
                logger.warning(
                    "Strategy index %d out of bounds for actions %s",
                    strategy_index,
                    actions,
                )

        if pruning_occurred == 1:
            node.pruned = True

        for i in reversed(children_to_remove):
            del node.children[i]
            del node.actions[i]

    for child in node.children:
        if prune_tree_nodes(
            child, state_set, action, strategy_index, current_level + 1
        ):
            pruning_occurred = 1

    return pruning_occurred


def boolean_pruning(
    cgs: CGS,
    tree: Node,
    condition: str,
    action: str,
    strategy_index: int,
    model_path: str,
) -> int:
    """
    Prune tree based on boolean (propositional) condition.
    """
    states = ctl_model_checking_cached(str(condition), model_path, preloaded_model=cgs)

    if "res" in states and ": " in states["res"]:
        state_set = parse_state_set_literal(states["res"].split(": ")[1])
    else:
        logger.warning(
            "Boolean pruning failed to parse states for condition '%s'", condition
        )
        state_set = set()

    logger.debug(
        "States where '%s' holds: %s (count: %d)", condition, state_set, len(state_set)
    )

    return prune_tree_nodes(tree, state_set, action, strategy_index)


def idle_pruning(
    cgs: CGS,
    tree: Node,
    state_set: Set[str],
    action: str,
    strategy_index: int,
    model_path: str,
) -> int:
    """
    Prune tree with idle action for states not covered by other conditions.
    """
    return prune_tree_nodes(tree, state_set, action, strategy_index)
