"""
Strategy initialization for NatATL Recall model checker.

This module handles model loading, validation, and formula parsing for
recall strategy verification.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import (
    get_agents_from_natatl,
    get_k_value,
    natatl_to_ctl,
)
from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.game_structures.cgs import (
    CGSProtocol,
    cgs_validation,
)

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str, cgs: Optional[CGSProtocol] = None
) -> Tuple[
    int,
    Dict[str, List[str]],
    List[List[str]],
    List[str],
    str,
    List[int],
    str,
    Any,
]:
    """
    Initialize model and parse NatATL formula for recall verification.

    Performs model loading, validation, formula parsing, and extracts all
    parameters needed for strategy generation.

    Args:
        model_path: Path to the CGS model file
        formula: NatATL formula string
        cgs: Optional existing CGS object (avoids reloading)

    Returns:
        Tuple of (k, agent_actions, actions_list, atomic_propositions,
                 CTLformula, agents, filename, model_parser)
    """
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")

    if cgs:
        model_parser = cgs
        # Ensure model content is loaded if using a pre-existing parser instance
        if not hasattr(model_parser, "states") or not model_parser.states:
            model_parser.read_file(filename)
        n = model_parser.get_number_of_agents()
        cgs_validation.validate_nat_idle_requirements(model_parser.graph, n)
        cgs_validation.validate_recall_structure(model_parser.graph, n)
    else:
        model_parser = create_model_parser_for_logic(filename, "NatATL")
        model_parser.read_file(filename)
        n = model_parser.get_number_of_agents()
        cgs_validation.validate_nat_idle_requirements(model_parser.graph, n)
        cgs_validation.validate_recall_structure(model_parser.graph, n)

    CTLformula = natatl_to_ctl(formula)
    logger.debug("NatATL formula: %s", formula)
    logger.debug("Converted CTL formula: %s", CTLformula)

    k = get_k_value(formula)
    logger.debug("States: %s", model_parser.get_states())
    logger.debug("Proposition matrix: %s", model_parser.get_matrix_proposition())

    agents = get_agents_from_natatl(formula)
    logger.debug("Involved agents: %s", agents)

    actions_per_agent = model_parser.get_actions(agents)
    logger.debug("Actions per agent: %s", actions_per_agent)

    agent_actions = {}
    for agent_key in actions_per_agent.keys():
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    actions_list = list(agent_actions.values())
    atomic_propositions = model_parser.get_atomic_prop()
    logger.debug("Atomic propositions: %s", atomic_propositions)

    return (
        k,
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        filename,
        model_parser,
    )
