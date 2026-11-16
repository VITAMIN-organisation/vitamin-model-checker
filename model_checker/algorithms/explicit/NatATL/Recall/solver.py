"""Strategy search for NatATL Recall: recall strategy profiles of the coalition,
smallest total size first, each checked on the model restricted to it."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.patterns import (
    enumerate_patterns,
    true_letter,
)
from model_checker.algorithms.explicit.NatATL.Recall.product import build_product
from model_checker.algorithms.explicit.NatATL.Recall.strategies import (
    RecallStrategy,
    agent_strategies,
    valid_rules,
)
from model_checker.algorithms.explicit.NatATL.Recall.validity import (
    last_states,
    successors,
)
from model_checker.algorithms.explicit.shared.natural_strategies import (
    available_actions,
    enumerate_conditions,
    goal_holds_on,
    parse_rows,
    smallest_winning_profile,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def solve_natatl_recall(
    k: int,
    ctl_formula: str,
    agents: list[int],
    cgs: CGSProtocol,
    model_path: str,
) -> dict[str, Any]:
    """Whether the coalition has a recall strategy profile of total size at most k
    that enforces the goal, with the smallest such profile."""
    # Every other member needs at least its idle rule, so one member's other rules
    # have at most k - len(agents) symbols; a negative budget gives no profile.
    budget = k - len(agents)
    letters = enumerate_conditions(cgs, budget) + [true_letter(cgs.states)]
    parsed_rows = parse_rows(cgs)
    succ = successors(cgs.states, parsed_rows)
    ends = {
        pattern: last_states(pattern, succ)
        for pattern in enumerate_patterns(letters, budget)
    }
    per_agent = [
        agent_strategies(
            valid_rules(ends, available_actions(cgs.states, parsed_rows, agent)),
            budget + 1,
        )
        for agent in agents
    ]
    # Many profiles restrict the model the same way, and CTL reads only the graph
    # and the labels of the product.
    verdicts: dict[tuple, bool] = {}

    def wins(profile: tuple[RecallStrategy, ...]) -> bool:
        product = build_product(cgs, parsed_rows, agents, profile)
        key = (
            tuple(map(tuple, product.graph)),
            tuple(map(tuple, product.matrix_prop)),
        )
        if key not in verdicts:
            verdicts[key] = goal_holds_on(product, ctl_formula, model_path)
        return verdicts[key]

    logger.info("Starting NatATL Recall verification (Bound k=%d)", k)
    return smallest_winning_profile(
        per_agent, k, wins, RecallStrategy.as_pairs, cgs.initial_state
    )
