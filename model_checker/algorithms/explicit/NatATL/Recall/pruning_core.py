"""
Core pruning orchestration for NatATL Recall model checker.

This module implements the main pruning function that coordinates boolean
and regex pruning, validates strategies, and performs CTL verification.
"""

import logging
from typing import Dict, Set

from model_checker.algorithms.explicit.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Recall.boolean_pruning import (
    boolean_pruning,
    idle_pruning,
)
from model_checker.algorithms.explicit.NatATL.Recall.condition_cache import (
    ctl_model_checking_cached,
)
from model_checker.algorithms.explicit.NatATL.Recall.regex_parser import (
    is_regex_or_boolean_formula,
)
from model_checker.algorithms.explicit.NatATL.Recall.regex_pruning import (
    regex_pruning,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_building import (
    build_cgs_from_tree,
    tree_to_initial_CGS,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import (
    Node,
    are_all_nodes_pruned,
    get_states_from_tree,
    rename_nodes,
    reset_pruned_flag,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_traversal import (
    depth_first_search,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs.cgs import CGS

logger = logging.getLogger(__name__)


def legit_strategy_check(
    cgs: CGS,
    tree: Node,
    condition: str,
    action: str,
    strategy_index: int,
    model_path: str,
) -> bool:
    """
    Verify that a strategy is valid before applying pruning.

    Checks that for every state matching the condition, the agent has the
    required action available in at least one transition.
    """
    condition_type = is_regex_or_boolean_formula(condition)

    if condition_type == "Boolean Formula":
        states = ctl_model_checking_cached(condition, model_path, preloaded_model=cgs)
        if "error" in states:
            error_msg = states["error"]["message"]
            raise ValueError(f"Error in strategy condition '{condition}': {error_msg}")

        if "res" in states and ": " in states["res"]:
            state_set = parse_state_set_literal(states["res"].split(": ")[1])
        else:
            state_set = set()

        logger.debug("States where '%s' holds: %d", condition, len(state_set))

    elif condition_type == "Regex":
        state_set = set()
        path = depth_first_search(
            cgs, tree, condition, len(tree.children), len(tree.children)
        )
        if path:
            state_set.update(path)
        logger.debug("States where regex '%s' matched: %s", condition, state_set)
    else:
        raise ValueError(f"Unrecognized condition type: {condition_type}")

    if not state_set:
        return True

    def check_action_exists(
        node: Node, state_set: Set[str], action: str, strategy_index: int
    ) -> bool:
        """Check if at least one matching action exists in matching states."""
        if node.state in state_set:
            action_exists = False
            for _i, (_child, actions) in enumerate(zip(node.children, node.actions)):
                if strategy_index - 1 < len(actions):
                    if actions[strategy_index - 1] == action:
                        action_exists = True
                        break
            if not action_exists:
                return False

        for child in node.children:
            if not check_action_exists(child, state_set, action, strategy_index):
                return False

        return True

    return check_action_exists(tree, state_set, action, strategy_index)


def pruning(
    cgs: CGS,
    tree: Node,
    height: int,
    model_path: str,
    CTLformula: str,
    *strategies: Dict,
) -> bool:
    """
    Main pruning function for recall NatATL: apply all strategies and verify formula.

    Applies each agent's strategy to prune the execution tree, then converts
    the pruned tree back to a CGS and runs CTL model checking.

    Args:
        cgs: CGS model object
        tree: Root node of execution tree
        height: Maximum tree height
        model_path: Path to model file
        CTLformula: CTL formula to verify (converted from NatATL)
        *strategies: Strategy dicts, one per agent

    Returns:
        True if formula holds in initial state, False otherwise
    """
    pruning_flag = 0

    for strategy_index, strategy in enumerate(strategies, start=1):
        for _iteration, (condition, action) in enumerate(
            strategy["condition_action_pairs"]
        ):
            if legit_strategy_check(
                cgs, tree, condition, action, strategy_index, model_path
            ):
                condition_type = is_regex_or_boolean_formula(condition)

                if condition_type == "Boolean Formula":
                    pruning_flag = boolean_pruning(
                        cgs, tree, condition, action, strategy_index, model_path
                    )
                elif condition_type == "Regex":
                    pruning_flag = regex_pruning(
                        cgs, tree, condition, action, strategy_index, height
                    )

                if are_all_nodes_pruned(tree):
                    pass
                else:
                    pruning_flag = 0
            else:
                logger.debug(
                    "Strategy validation FAILED for action '%s' "
                    "with condition '%s' (agent %d)",
                    action,
                    condition,
                    strategy_index,
                )
                return False

        if pruning_flag == 0:
            pruning_flag = idle_pruning(
                cgs, tree, set(cgs.get_states()), "I", strategy_index, model_path
            )

        reset_pruned_flag(tree)

    rename_nodes(tree)
    tree_states = get_states_from_tree(tree)

    unwinded_CGS = tree_to_initial_CGS(
        tree, tree_states, cgs.get_number_of_agents(), height
    )

    pruned_cgs = build_cgs_from_tree(cgs, tree, tree_states, unwinded_CGS)
    result = model_checking(CTLformula, model_path, preloaded_model=pruned_cgs)

    if "error" in result:
        logger.warning("CTL verification returned error: %s", result["error"])
        prefix = "[SEMANTIC] " if result["error"]["type"] == "semantic" else ""
        raise ValueError(f"{prefix}Recalled CTL error: {result['error']['message']}")

    if result.get("initial_state") == f"Initial state {pruned_cgs.initial_state}: True":
        return True
    return False
