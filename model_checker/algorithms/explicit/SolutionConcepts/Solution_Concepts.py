"""Nash Equilibrium verification.

Verifies Nash Equilibrium properties by checking for profitable unilateral deviations.
"""

import logging
from typing import Dict, List, Tuple

from model_checker.algorithms.explicit.LTL.pruning import pruning
from model_checker.algorithms.explicit.LTL.strategies import (
    generate_deviations_for_agent,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def is_not_nash(
    model: str,
    cgs: CGSProtocol,
    agents: List[str],
    ctl_formula: str,
    current_strategy: List[Tuple[str, str]],
    bound: int,
    agent_actions: Dict[str, List[str]],
    atomic_propositions: List[str],
) -> bool:
    """Checks if the strategy profile is NOT a Nash Equilibrium.

    Iterates through each agent to find any profitable unilateral deviation.

    Args:
        model: Path to model file.
        cgs: Concurrent Game Structure object.
        agents: List of agent names.
        ctl_formula: CTL formula to verify.
        current_strategy: Current strategy profile.
        bound: Strategy complexity bound.
        agent_actions: Dictionary of agent actions.
        atomic_propositions: List of atomic propositions.

    Returns:
        True if a profitable deviation is found (NOT Nash), False otherwise.
    """
    for agent_index, agent in enumerate(agents):
        logger.debug("Checking deviations for agent %s (Index: %d)", agent, agent_index)

        if not pruning(cgs, model, agents, ctl_formula, current_strategy):
            agent_key = f"actions_agent{agent}"
            agent_actions_for_agent = agent_actions.get(agent_key, [])

            logger.debug("Agent %s actions: %s", agent, agent_actions_for_agent)

            deviations = generate_deviations_for_agent(
                current_strategy[agent_index],
                bound,
                agent_actions_for_agent,
                atomic_propositions,
            )

            for deviation in deviations:
                original_strategy_part = current_strategy[agent_index]

                current_strategy[agent_index] = deviation

                if pruning(cgs, model, agents, ctl_formula, current_strategy):
                    logger.info(
                        "Profitable deviation found for agent %s: %s", agent, deviation
                    )
                    current_strategy[agent_index] = original_strategy_part
                    return True

                current_strategy[agent_index] = original_strategy_part

    return False


def exists_nash(
    cgs: CGSProtocol,
    agents: List[str],
    ctl_formula: str,
    current_strategy: List[Tuple[str, str]],
    bound: int,
    agent_actions: Dict[str, List[str]],
    atomic_propositions: List[str],
) -> bool:
    """Checks if the strategy profile IS a Nash Equilibrium.

    Inverse of is_not_nash.
    """
    return not is_not_nash(
        model=(
            cgs.filename if hasattr(cgs, "filename") else ""
        ),  # Best effort to get filename
        cgs=cgs,
        agents=agents,
        ctl_formula=ctl_formula,
        current_strategy=current_strategy,
        bound=bound,
        agent_actions=agent_actions,
        atomic_propositions=atomic_propositions,
    )
