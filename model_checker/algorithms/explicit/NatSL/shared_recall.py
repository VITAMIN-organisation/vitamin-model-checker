"""
Shared Recall-based NatATL logic for Strategy Logic (NatSL) semantics.

This module provides common building blocks for both Sequential and Alternated
NatSL verification, reducing duplication of strategy and tree management.
"""

import copy
import logging
import time
from typing import Any, List, Optional, Tuple

from model_checker.algorithms.explicit.NatATL.Recall.condition_generation import (
    create_reg_exp,
)
from model_checker.algorithms.explicit.NatATL.Recall.pruning_core import (
    pruning,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_generation import (
    generate_guarded_action_pairs,
    generate_strategies,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_initialization import (
    initialize,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_building import (
    build_tree_from_CGS,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def universal_natatl_recall(
    trees: List[Any],
    model_path: str,
    formula: str,
    num_agents: int,
    height: int,
    start_time: float,
    cgs: Optional[CGSProtocol] = None,
) -> bool:
    """
    Check universal strategies against a set of pruned trees.

    Args:
        trees: List of trees pruned by existential strategies
        model_path: Path to model file
        formula: NatATL formula for universal agents
        num_agents: Number of universal agents
        height: Tree height for pruning
        start_time: Verification start time (for timing)
        cgs: The CGS model object (optional, reused if provided)

    Returns:
        True if any tree survives all universal strategies, False otherwise
    """
    if num_agents == 0:
        logger.debug("No universal agents - vacuously true")
        return True

    if not trees:
        return False

    (
        k,
        _,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        filename,
        cgs,
    ) = initialize(model_path, formula, cgs=cgs)

    reg_exp = create_reg_exp(k, atomic_propositions)
    cartesian_products = generate_guarded_action_pairs(
        list(reg_exp), list(actions_list)
    )

    found_solution = False

    for tree_index, tree in enumerate(trees):
        tree_valid = True
        strategies_iterator = generate_strategies(cartesian_products, k, agents, False)

        for universal_strategy in strategies_iterator:
            # We deepcopy the tree each time because pruning modifies it
            tree_test = copy.deepcopy(tree)

            if not pruning(
                cgs, tree_test, height, filename, CTLformula, *universal_strategy
            ):
                logger.debug(
                    "Tree %d invalidated by universal strategy %s",
                    tree_index,
                    universal_strategy,
                )
                tree_valid = False
                break

        if tree_valid:
            logger.info("Solution found with tree %d", tree_index + 1)
            found_solution = True
            break

    elapsed = time.time() - start_time
    logger.debug("Elapsed time for universal check: %.3f seconds", elapsed)

    return found_solution


def existential_natatl_sequential(
    model_path: str, formula: str
) -> Tuple[bool, List[Any], int, Any]:
    """
    Search for existential strategies and collect pruned trees (Sequential).
    """
    found_solution = False
    (
        k,
        _,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        filename,
        cgs,
    ) = initialize(model_path, formula)

    i = 1
    height = max(3, k)
    pruned_trees = []

    while not found_solution and i <= k:
        try:
            tree = build_tree_from_CGS(cgs, cgs.get_states(), height)
        except Exception:
            return (False, [], height, cgs)

        reg_exp = create_reg_exp(i, atomic_propositions)
        cartesian_products = generate_guarded_action_pairs(
            list(reg_exp), list(actions_list)
        )
        strategies_iterator = generate_strategies(cartesian_products, i, agents, False)

        for collective_strategy in strategies_iterator:
            tree_copy = copy.deepcopy(tree)
            if pruning(
                cgs, tree_copy, height, filename, CTLformula, *collective_strategy
            ):
                return (True, [], height, cgs)
            pruned_trees.append(tree_copy)
        i += 1

    return (False, pruned_trees, height, cgs)


def existential_natatl_alternated(
    model_path: str,
    existential_formula: str,
    universal_formula: str,
    start_time: float,
) -> bool:
    """
    Search for existential strategy that survives all universal challenges (Alternated).
    """
    (
        k,
        _,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        filename,
        cgs,
    ) = initialize(model_path, existential_formula)

    height = max(3, k)
    found_solution = False
    i = 1

    while not found_solution and i <= k:
        try:
            tree = build_tree_from_CGS(cgs, cgs.get_states(), height)
        except Exception:
            return False

        reg_exp = create_reg_exp(i, atomic_propositions)
        cartesian_products = generate_guarded_action_pairs(
            list(reg_exp), list(actions_list)
        )
        strategies_iterator = generate_strategies(cartesian_products, i, agents, False)

        for collective_strategy in strategies_iterator:
            tree_copy = copy.deepcopy(tree)
            if pruning(
                cgs, tree_copy, height, filename, CTLformula, *collective_strategy
            ):
                return True

            if universal_natatl_recall(
                [tree_copy], model_path, universal_formula, 1, height, start_time, cgs
            ):
                return True
        i += 1

    return False
