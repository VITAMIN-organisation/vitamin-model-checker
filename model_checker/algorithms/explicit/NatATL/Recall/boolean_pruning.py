"""Boolean pruning for NatATL Recall: CTL finds where a condition holds, and the
execution tree is pruned there."""

import logging

from model_checker.algorithms.explicit.NatATL.Recall.condition_cache import (
    ctl_model_checking_cached,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.algorithms.explicit.shared.result_formatters import (
    states_of_result,
)
from model_checker.parsers.game_structures.cgs.cgs import CGS

logger = logging.getLogger(__name__)


def prune_tree_nodes(
    node: Node,
    state_set: set[str],
    action: str,
    strategy_index: int,
    current_level: int = 0,
) -> int:
    """Remove the children whose agent action does not match."""
    pruning_occurred = 0

    if node.state in state_set:
        children_to_remove = []
        for i, (_child, actions) in enumerate(
            zip(node.children, node.actions, strict=False)
        ):
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
    """Prune the tree by a boolean condition."""
    states = ctl_model_checking_cached(str(condition), model_path, preloaded_model=cgs)
    state_set = states_of_result(states, str(condition))

    logger.debug(
        "States where '%s' holds: %s (count: %d)", condition, state_set, len(state_set)
    )

    return prune_tree_nodes(tree, state_set, action, strategy_index)
