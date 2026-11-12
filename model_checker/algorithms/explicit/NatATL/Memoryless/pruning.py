"""Matrix-based pruning for NatATL Memoryless.

A memoryless strategy depends only on the current state, so its condition-action
rules cut the CGS transition matrix directly, with no tree; CTL model checking then
runs on the pruned model.
"""

import copy
import logging
from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    initial_state_holds,
    states_of_result,
)
from model_checker.parsers.game_structures.cgs import CGS

logger = logging.getLogger(__name__)


def apply_first_matching_rules(
    cgs: CGS,
    model_path: str,
    agents: list[int],
    strategy_index: int,
    strategy: dict[str, Any],
    graph: list[list],
) -> tuple[list[list], set[str]]:
    """Cut `graph` by one strategy, in place, and return it with the states the rules
    covered. A state follows the first rule whose condition holds there, so a rule
    applies only to the states no earlier rule covered, and a rule that holds in no
    such state selects nothing."""
    covered_states: set[str] = set()
    # Cache model_checking results for conditions to avoid redundant CTL calls
    cache = vars(cgs).setdefault("_condition_cache", {})
    for condition, action in strategy["condition_action_pairs"]:
        cache_key = (condition, model_path)
        if cache_key not in cache:
            cache[cache_key] = model_checking(
                condition, model_path, preloaded_model=cgs
            )
        applicable_states = (
            states_of_result(cache[cache_key], condition) - covered_states
        )
        if not applicable_states:
            continue
        graph = modify_matrix(
            graph,
            applicable_states,
            action,
            strategy_index,
            agents,
            num_agents=cgs.get_number_of_agents(),
            state_to_index=cgs.state_to_index,
            in_place=True,
        )
        covered_states.update(applicable_states)
    return graph, covered_states


def process_transition_matrix_data_fixed(
    cgs: CGS, model_path: str, agents: list[int], *strategies: dict[str, Any]
) -> list[list]:
    """Pruning with corrected state coverage logic: the states no rule covers play
    idle."""
    graph = [row[:] for row in cgs.graph]

    for strategy_index, strategy in enumerate(strategies, start=1):
        graph, covered_states = apply_first_matching_rules(
            cgs, model_path, agents, strategy_index, strategy, graph
        )
        remaining = set(cgs.states) - covered_states
        if remaining:
            graph = modify_matrix(
                graph,
                remaining,
                "I",
                strategy_index,
                agents,
                num_agents=cgs.get_number_of_agents(),
                state_to_index=cgs.state_to_index,
                in_place=True,
            )

    return graph


def pruning(
    cgs: CGS, model_path: str, agents: list[int], formula: str, current_agents: list
) -> bool:
    """Prune the model to a strategy profile and run CTL on the result.

    Returns True when the initial state satisfies the formula on the pruned model.
    """
    # Isolate pruned model from the shared CGS used across strategy candidates.
    cgs1 = copy.deepcopy(cgs)
    cgs1.graph = process_transition_matrix_data_fixed(
        cgs, model_path, agents, *current_agents
    )

    return initial_state_holds(
        model_checking(formula, model_path, preloaded_model=cgs1), formula
    )
