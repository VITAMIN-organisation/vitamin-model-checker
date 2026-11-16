"""Strategy search for NatATL memoryless verification: natural strategy profiles of
the coalition, smallest total size first, each checked on the model it prunes."""

import copy
import logging
from typing import Any

from model_checker.algorithms.explicit.shared.natural_strategies import (
    agent_strategies,
    available_actions,
    enumerate_conditions,
    goal_holds_on,
    parse_rows,
    restrict_to_profile,
    smallest_winning_profile,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def _profile_wins(cgs, parsed_rows, agents, profile, ctl_formula, model_path) -> bool:
    """True when the CTL goal holds at the initial state of the model pruned to the
    coalition's profile."""
    # CTL only reads the model, and its edge caches are keyed by the graph object.
    pruned = copy.copy(cgs)
    pruned.graph = restrict_to_profile(cgs.states, parsed_rows, agents, profile)
    return goal_holds_on(pruned, ctl_formula, model_path)


def solve_natatl_memoryless(
    k: int,
    ctl_formula: str,
    agents: list[int],
    cgs: CGSProtocol,
    model_path: str,
) -> dict[str, Any]:
    """Whether the coalition has a natural strategy profile of total size at most k
    that enforces the goal, with the smallest such profile."""
    # Every other member needs at least its true rule, so one condition is at most
    # k - len(agents) symbols; with k below the coalition size no profile exists.
    conditions = enumerate_conditions(cgs, k - len(agents))
    parsed_rows = parse_rows(cgs)
    per_agent = [
        agent_strategies(
            conditions,
            available_actions(cgs.states, parsed_rows, agent),
            k - len(agents) + 1,
        )
        for agent in agents
    ]
    logger.info("Starting NatATL Memoryless verification (Bound k=%d)", k)

    return smallest_winning_profile(
        per_agent,
        k,
        lambda profile: _profile_wins(
            cgs, parsed_rows, agents, profile, ctl_formula, model_path
        ),
        lambda strategy: list(strategy.rules),
        cgs.initial_state,
    )
