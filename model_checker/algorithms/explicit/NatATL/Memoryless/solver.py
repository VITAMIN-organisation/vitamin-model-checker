"""
Solver module for NatATL Memoryless verification.

This module orchestrates the strategy enumeration and verification loop,
iterating through complexity bounds and checking strategies via pruning.
"""

import logging
from typing import Any, Dict, List

from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
    pruning,
)
from model_checker.algorithms.explicit.shared.strategies_base import (
    generate_guarded_action_pairs,
    generate_strategies,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def solve_natatl_memoryless(
    k: int,
    agent_actions: Dict[str, List[str]],
    actions_list: List[List[str]],
    atomic_propositions: List[str],
    CTLformula: str,
    agents: List[int],
    cgs: CGSProtocol,
    model_path: str,
) -> Dict[str, Any]:
    """
    Solve NatATL Memoryless verification by enumerating and checking strategies.

    This function implements the core verification loop:
    1. Iterate through complexity bounds from 1 to k
    2. For each bound, generate all possible strategies
    3. For each strategy, apply pruning and verify the formula
    4. Return the first winning strategy found (early termination)

    Args:
        k: Maximum complexity bound
        agent_actions: Dictionary mapping agent keys to their available actions
        actions_list: List of action lists for each agent
        atomic_propositions: List of atomic propositions in the model
        CTLformula: CTL formula to verify (converted from NatATL)
        agents: List of agent numbers in the coalition
        cgs: CGS model object
        model_path: Path to model file

    Returns:
        Dictionary with Satisfiability, Complexity Bound, and Winning Strategy
    """
    found_solution = False
    result: Dict[str, Any] = {}

    i = 1
    logger.info("Starting NatATL Memoryless verification (Bound k=%d)", k)

    while not found_solution and i <= k:
        logger.debug("Checking strategies at complexity level %d", i)

        # Generate guarded action pairs for each agent
        cartesian_products = generate_guarded_action_pairs(
            i, agent_actions, actions_list, atomic_propositions
        )

        # Generate strategies for this complexity level
        strategies_generator = generate_strategies(
            cartesian_products, i, agents, found_solution
        )

        # Check each strategy via pruning & model checking
        for current_strategy in strategies_generator:
            found_solution = pruning(
                cgs, model_path, agents, CTLformula, current_strategy
            )

            if found_solution:
                logger.info("Solution found with strategy: %s", current_strategy)
                result["Satisfiability"] = True
                result["Complexity Bound"] = i
                result["Winning Strategy per agent"] = current_strategy
                break

        i += 1

    if not found_solution:
        logger.info("No solution found after checking bound k=%d", k)
        result["Satisfiability"] = False
        result["Complexity Bound"] = k

    # Add standard result fields for backend compatibility
    initial_state = cgs.initial_state if hasattr(cgs, "initial_state") else "s0"
    is_sat = result.get("Satisfiability", False)
    result["res"] = f"Result: {is_sat}"
    result["initial_state"] = f"Initial state {initial_state}: {is_sat}"

    return result
