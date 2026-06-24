"""
NatATL Recall solver: strategy enumeration and verification loop.

Enumerates recall strategies using tree-based pruning rather than
matrix-based pruning, returning the first winning strategy found.
"""

import copy
import logging
import time
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.condition_generation import (  # noqa: E501
    create_reg_exp,
)
from model_checker.algorithms.explicit.NatATL.Recall.pruning_core import (
    pruning,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_generation import (  # noqa: E501
    generate_guarded_action_pairs,
    generate_strategies,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_building import (
    build_tree_from_CGS,
)

logger = logging.getLogger(__name__)

INITIAL_HEIGHT = 4


def solve_natatl_recall(
    k: int,
    agent_actions: dict[str, list[str]],
    actions_list: list[list[str]],
    atomic_propositions: list[str],
    CTLformula: str,
    agents: list[int],
    model_parser: Any,
    filename: str,
) -> dict[str, Any]:
    """
    Solve NatATL Recall verification by enumerating and checking strategies.

    Iterates complexity bounds from 1 to k, generates all strategies (with
    regex conditions), applies tree-based pruning, and returns the first
    winning strategy found.

    Key differences from Memoryless:
    - Uses tree-based pruning instead of matrix-based
    - Supports regex conditions in addition to boolean formulas
    - Builds execution tree once per complexity level and deep-copies for each strategy

    Args:
        k: Maximum complexity bound
        agent_actions: Dictionary mapping agent keys to their available actions
        actions_list: List of action lists for each agent
        atomic_propositions: List of atomic propositions in the model
        CTLformula: CTL formula to verify (converted from NatATL)
        agents: List of agent numbers in the coalition
        model_parser: Model parser object (CGS)
        filename: Path to model file

    Returns:
        Dictionary with Satisfiability, Complexity Bound, and Winning Strategy
    """
    start_time = time.time()
    found_solution = False
    result: dict[str, Any] = {}

    i = 1
    height = INITIAL_HEIGHT

    logger.info("Starting NatATL Recall verification (Bound k=%d)", k)

    while not found_solution and i <= k:
        logger.debug("Checking strategies at complexity level %d", i)

        # Build tree once per complexity level and deepcopy for each strategy.
        # Pruning modifies the tree in-place, so we need a fresh copy per verification.
        if i == 1:
            states = model_parser.states
            base_tree = build_tree_from_CGS(model_parser, states, height)

        # Generate regex conditions for this complexity level
        reg_exp = create_reg_exp(i, atomic_propositions)
        conditions = list(reg_exp)
        actions = list(actions_list)
        cartesian_products = generate_guarded_action_pairs(conditions, actions)

        # Generate strategies for this complexity level
        strategies_iterator = generate_strategies(
            cartesian_products, i, agents, found_solution
        )

        # Check each strategy via tree-based pruning & model checking
        for collective_strategy in strategies_iterator:
            # Deep copy crucial here as pruning mutates tree
            tree_copy = copy.deepcopy(base_tree)

            if pruning(
                model_parser,
                tree_copy,
                height,
                filename,
                CTLformula,
                *collective_strategy,
            ):
                logger.info("Solution found with strategy: %s", collective_strategy)
                found_solution = True
                result["Satisfiability"] = True
                result["Complexity Bound"] = i
                result["Winning Strategy per agent"] = collective_strategy
                break

        i += 1

    if not found_solution:
        logger.info("No solution found after checking bound k=%d", k)
        result["Satisfiability"] = False
        result["Complexity Bound"] = k

    # Add standard result fields for backend compatibility
    initial_state = (
        model_parser.initial_state if hasattr(model_parser, "initial_state") else "s0"
    )
    is_sat = result.get("Satisfiability", False)
    result["res"] = f"Result: {is_sat}"
    result["initial_state"] = f"Initial state {initial_state}: {is_sat}"

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info("Total verification time: %.3f seconds", elapsed_time)

    return result
