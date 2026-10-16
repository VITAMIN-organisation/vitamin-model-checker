
"""Lazy cost-ordered search for NatATL memoryless strategies."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Memoryless.lazy_generation import (
    collective_strategies,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
    pruning,
)
from model_checker.algorithms.explicit.NatATL.strategy_complexity import (
    individual_complexity,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)


def solve_natatl_memoryless(
    k: int,
    agent_actions: dict[str, list[str]],
    actions_list: list[list[str]],
    atomic_propositions: list[str],
    CTLformula: str,
    agents: list[int],
    cgs: CGSProtocol,
    model_path: str,
) -> dict[str, Any]:
    """Search profiles by increasing collective complexity.

    agent_actions is retained for the NatATLF compatibility calling convention;
    actions_list is the authoritative per-agent action inventory in this solver.
    """

    if k < 0:
        raise ValueError("Complexity bound must be nonnegative")

    if len(agents) != len(actions_list):
        raise ValueError("Mismatch between agents and action lists")

    if len(set(agents)) != len(agents):
        raise ValueError("Repeated coalition agent")

    # Wildcard semantics are not yet supported by strict pruning.
    if any(
        isinstance(cell, str) and "*" in cell
        for row in cgs.graph
        for cell in row
    ):
        raise ValueError(
            "Unsupported NatATL wildcard joint action in model"
        )

    actions_by_agent = {
        agent: list(dict.fromkeys(actions))
        for agent, actions in zip(agents, actions_list, strict=True)
    }

    checked = 0
    rejected = 0
    initial = str(getattr(cgs, "initial_state", "s0"))

    logger.info(
        "Starting NatATL lazy memoryless search: k=%d",
        k,
    )

    generator = collective_strategies(
        agents=agents,
        actions_by_agent=actions_by_agent,
        propositions=atomic_propositions,
        bound=k,
    )

    for candidate in generator:

        # Sum of individual complexities.
        cost = sum(
            individual_complexity(
                strategy["condition_action_pairs"]
            )
            for strategy in candidate
        )

        if cost > k:
            raise AssertionError(
                "Generator exceeded the collective complexity bound"
            )

        try:
            winning = pruning(
                cgs,
                model_path,
                agents,
                CTLformula,
                candidate,
            )

        except ValueError as exc:
            # An unavailable action makes this candidate
            # inadmissible, not the entire model.
            if "not enabled" not in str(exc).lower():
                raise

            rejected += 1
            continue

        checked += 1

        if winning:
            logger.info(
                "Winning collective strategy found at cost %d",
                cost,
            )

            return {
                "Satisfiability": True,
                "Complexity Bound": k,
                "Requested Complexity Bound": k,
                "Witness Complexity": cost,
                "Winning Strategy per agent": candidate,
                "Candidates Checked": checked,
                "Candidates Rejected": rejected,
                "res": "Result: True",
                "initial_state": (
                    f"Initial state {initial}: True"
                ),
            }

    logger.info("Search exhausted up to bound k=%d", k)

    return {
        "Satisfiability": False,
        "Complexity Bound": k,
        "Requested Complexity Bound": k,
        "Candidates Checked": checked,
        "Candidates Rejected": rejected,
        "res": "Result: False",
        "initial_state": (
            f"Initial state {initial}: False"
        ),
    }
