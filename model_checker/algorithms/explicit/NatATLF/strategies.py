"""
Strategy generation for NatATLF model checker.

NatATLF (NatATL with Fixed-point semantics) uses the same strategy generation
approach as NatATL Memoryless. This module re-exports the shared utilities
and provides the initialize function.

Note: This module intentionally mirrors NatATL/Memoryless/strategies.py
as both logics share the same strategy generation algorithm.
"""

import logging
import os
from typing import Any, Dict, List, Tuple

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import (
    get_agents_from_natatl,
    get_k_value,
    natatl_to_ctl,
)
from model_checker.parsers.game_structures.cgs import CGS, cgs_validation

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str
) -> Tuple[int, Dict[str, Any], List[Any], List[Any], str, List[int], CGS]:
    """
    Initialize model and parse NatATL formula for fixed-point verification.

    Performs the following setup:
    1. Loads the CGS model from file
    2. Validates NAT compliance (action patterns)
    3. Converts NatATL formula to equivalent CTL formula
    4. Extracts agents, actions, and atomic propositions

    Args:
        model_path: Path to the CGS model file
        formula: NatATL formula string (e.g., "<{1}, 2>Fa")

    Returns:
        Tuple of (k, agent_actions, actions_list, atomic_propositions,
                 CTLformula, agents, cgs) where:
        - k: Complexity bound from formula
        - agent_actions: Dict mapping agent keys to action lists
        - actions_list: Flat list of action sets per agent
        - atomic_propositions: List of atomic props in model
        - CTLformula: Converted CTL formula for verification
        - agents: List of agent indices from formula
        - cgs: Loaded CGS model object

    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")

    cgs = CGS()
    cgs.read_file(filename)
    cgs_validation.validate_nat_idle_requirements(cgs.graph, cgs.get_number_of_agents())
    CTLformula = natatl_to_ctl(formula)
    logger.debug("NatATL formula: %s", formula)
    logger.debug("Converted CTL formula: %s", CTLformula)

    k = get_k_value(formula)
    agents = get_agents_from_natatl(formula)
    logger.debug("Involved agents: %s", agents)

    actions_per_agent = cgs.get_actions(agents)
    logger.debug("Actions per agent: %s", actions_per_agent)

    agent_actions = {}
    for _i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    actions_list = list(agent_actions.values())
    atomic_propositions = cgs.get_atomic_prop()
    logger.debug("Atomic propositions: %s", atomic_propositions)

    return k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs
