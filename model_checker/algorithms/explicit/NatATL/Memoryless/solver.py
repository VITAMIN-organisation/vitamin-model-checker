"""Strategy search for NatATL memoryless verification: natural strategy profiles of
the coalition, smallest total size first, each checked on the model it prunes."""

import copy
import logging
from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.shared.natural_strategies import (
    agent_strategies,
    available_actions,
    coalition_profiles,
    enumerate_conditions,
    parse_rows,
    restrict_to_profile,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    initial_state_holds,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol, cgs_validation

logger = logging.getLogger(__name__)


def _profile_wins(cgs, parsed_rows, agents, profile, ctl_formula, model_path) -> bool:
    """True when the CTL goal holds at the initial state of the model pruned to the
    coalition's profile. A profile that leaves a state with no move is skipped: the
    CTL check would read that dead end as a win for AF."""
    graph = restrict_to_profile(cgs.states, parsed_rows, agents, profile)
    if cgs_validation.validate_total_transitions(graph, cgs.states):
        return False
    # CTL only reads the model, and its edge caches are keyed by the graph object.
    pruned = copy.copy(cgs)
    pruned.graph = graph
    result = model_checking(ctl_formula, model_path, preloaded_model=pruned)
    return initial_state_holds(result, ctl_formula)


def solve_natatl_memoryless(
    k: int,
    ctl_formula: str,
    agents: list[int],
    cgs: CGSProtocol,
    model_path: str,
) -> dict[str, Any]:
    """Whether the coalition has a natural strategy profile of total size at most k
    that enforces the goal, with the smallest such profile."""
    if k < len(agents):
        raise ValueError(
            f"[VALIDATION] k = {k} is smaller than the coalition {agents}: each "
            "member's strategy has size at least 1, its true rule."
        )
    # Every other member needs at least its true rule, so one condition is at most
    # k - len(agents) symbols.
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

    result: dict[str, Any] = {"Satisfiability": False, "Complexity Bound": k}
    for total, profile in coalition_profiles(per_agent, k):
        if _profile_wins(cgs, parsed_rows, agents, profile, ctl_formula, model_path):
            logger.info("Solution found with strategy: %s", profile)
            result = {
                "Satisfiability": True,
                "Complexity Bound": total,
                "Winning Strategy per agent": [
                    {"condition_action_pairs": list(strategy.rules)}
                    for strategy in profile
                ],
            }
            break

    is_sat = result["Satisfiability"]
    result["res"] = f"Result: {is_sat}"
    result["initial_state"] = f"Initial state {cgs.initial_state}: {is_sat}"
    return result
