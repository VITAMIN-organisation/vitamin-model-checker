"""
Strategy generation for NatATL Memoryless model checker.

This module provides strategy initialization and generation specifically for
memoryless NatATL verification. It uses the shared strategy utilities and
adds NatATL-specific formula parsing and model initialization.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import (
    get_agents_from_natatl,
    get_k_value,
    natatl_to_ctl,
)
from model_checker.parsers.game_structures.cgs import CGS, cgs_validation

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str, cgs: Optional[CGS] = None
) -> Tuple[int, Dict[str, List[str]], List[List[str]], List[str], str, List[int], CGS]:
    """
    Initialize model and parse NatATL formula for memoryless verification.

    Args:
        model_path: Path to the CGS model file
        formula: NatATL formula string
        cgs: Optional existing CGS object (avoids reloading)

    Returns:
        Tuple of (k, agent_actions, actions_list, atomic_propositions,
                 CTLformula, agents, cgs)
    """
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Model file not found: {filename}")

    if cgs is None:
        cgs = CGS()
        try:
            cgs.read_file(filename)
        except Exception as e:
            logger.error("Failed to read model file %s: %s", filename, e)
            raise

    # Validate model structure for NatATL
    try:
        cgs_validation.validate_nat_idle_requirements(
            cgs.graph, cgs.get_number_of_agents()
        )
    except Exception as e:
        logger.warning("NatATL compliance validation warning: %s", e)

    # Transform NatATL formula into CTL formula for underlying model checking
    try:
        CTLformula = natatl_to_ctl(formula)
        logger.debug("NatATL formula: %s", formula)
        logger.debug("Converted CTL formula: %s", CTLformula)
    except Exception as e:
        logger.error("Failed to convert NatATL to CTL: %s", e)
        raise ValueError(f"Invalid NatATL formula format: {str(e)}") from e

    # Extract complexity bound from formula
    k = get_k_value(formula)

    # Get involved agents from the coalition operator
    agents = get_agents_from_natatl(formula)
    logger.debug("Involved agents: %s", agents)

    # Get available actions for each agent
    actions_per_agent = cgs.get_actions(agents)
    logger.debug("Actions per agent: %s", actions_per_agent)

    agent_actions = {}
    for agent_key in actions_per_agent.keys():
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    actions_list = list(agent_actions.values())
    atomic_propositions = cgs.get_atomic_prop()
    logger.debug("Atomic propositions: %s", atomic_propositions)

    return k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs
