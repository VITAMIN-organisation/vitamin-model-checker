"""Model and formula setup for NatATL memoryless verification."""

import logging
import os

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import prepare_natatl_formula
from model_checker.parsers.game_structures.cgs import CGS, cgs_actions, cgs_validation

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str, cgs: CGS | None = None
) -> tuple[int, dict[str, list[str]], list[list[str]], list[str], str, list[int], CGS]:
    """Load the model, parse NatATL, and return k, actions, CTL formula, and agents."""
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

    try:
        CTLformula, agents, k = prepare_natatl_formula(
            formula, cgs.get_number_of_agents()
        )
    except ValueError as e:
        logger.error("Failed to parse or convert NatATL: %s", e)
        raise ValueError(f"Invalid NatATL formula format: {str(e)}") from e

    logger.debug("Involved agents: %s", agents)

    cgs_actions.validate_agent_numbers(agents, cgs.get_number_of_agents())
    actions_per_agent = cgs_actions.extract_actions_for_agents(cgs.graph, agents)
    logger.debug("Actions per agent: %s", actions_per_agent)

    agent_actions = {}
    for agent_key in actions_per_agent.keys():
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    actions_list = list(agent_actions.values())
    atomic_propositions = cgs.atomic_propositions
    logger.debug("Atomic propositions: %s", atomic_propositions)

    return k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs
