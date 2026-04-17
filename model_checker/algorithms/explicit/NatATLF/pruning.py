"""
Pruning module for NatATLF model checker.

This module implements the matrix-based pruning algorithm for verifying
fixed-point NatATL strategies. Uses the same in-memory approach as NatATL
Memoryless: pruned CGS is passed to CTL model_checking via preloaded_model.
Reuses modify_matrix from NatATL.Memoryless.matrix_utils.
"""

import logging
from typing import Any, List

from model_checker.algorithms.explicit.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs import CGS, cgs_validation

logger = logging.getLogger(__name__)


def process_transition_matrix_data(
    cgs: CGS, model: str, agents: List[int], *strategies: Any
) -> List[List]:
    """
    Apply all agents' strategies to prune the transition matrix.

    Args:
        cgs: CGS model object with transition matrix
        model: Path to model file (for CTL checking of conditions)
        agents: List of agent numbers in the coalition
        *strategies: Variable number of strategy dicts, one per agent

    Returns:
        Pruned transition matrix with only strategy-compliant transitions
    """
    graph = cgs.transition_matrix
    label_matrix = cgs.create_label_matrix(graph)
    logger.debug("Initial transition matrix: %s", graph)

    actions_per_agent = cgs.get_actions(agents)
    agent_actions = {}
    for _i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    for agent_key in agent_actions:
        logger.debug("%s: %s", agent_key, agent_actions[agent_key])

    for strategy_index, strategy in enumerate(strategies, start=1):
        state_sets = set()
        temp = set()
        for iteration, (condition, action) in enumerate(
            strategy["condition_action_pairs"]
        ):
            if not hasattr(cgs, "_condition_cache"):
                cgs._condition_cache = {}
            cache_key = (condition, model)
            if cache_key not in cgs._condition_cache:
                cgs._condition_cache[cache_key] = model_checking(
                    condition, model, preloaded_model=cgs
                )
            states = cgs._condition_cache[cache_key]
            state_set = parse_state_set_literal(states["res"].split(": ")[1])

            if iteration > 0:
                if state_set:
                    temp = state_sets
                    state_sets = state_set - temp
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                graph = modify_matrix(
                    graph, label_matrix, state_sets, action, strategy_index, agents
                )
                logger.debug(
                    "Transition matrix after agent %d modification: %s",
                    strategy_index,
                    graph,
                )
            else:
                if state_set:
                    state_sets = state_set
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                graph = modify_matrix(
                    graph, label_matrix, state_sets, action, strategy_index, agents
                )
                logger.debug(
                    "Transition matrix after agent %d modification: %s",
                    strategy_index,
                    graph,
                )

    return graph


def pruning(
    cgs: CGS, model: str, agents: List[int], formula: str, current_agents: List
) -> bool:
    """
    Main pruning function: apply strategy and check if formula holds.

    Args:
        cgs: Original CGS model
        model: Path to model file
        agents: List of agent numbers in coalition
        formula: CTL formula to verify (converted from NatATL)
        current_agents: List of strategy dicts being tested

    Returns:
        True if the formula is satisfied in the initial state
    """
    cgs1 = CGS()
    cgs1.read_file(model)
    cgs1.graph = process_transition_matrix_data(cgs, model, agents, *current_agents)
    cgs_validation.validate_nat_idle_requirements(
        cgs1.graph, cgs.get_number_of_agents()
    )
    result = model_checking(formula, model, preloaded_model=cgs1)

    if "Initial state" in result.get("initial_state", "") and str(True) in result.get(
        "initial_state", ""
    ):
        return True
    return False
