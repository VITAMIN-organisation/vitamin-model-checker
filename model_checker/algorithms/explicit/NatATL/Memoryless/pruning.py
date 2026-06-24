"""
Matrix-based pruning for NatATL Memoryless verification.

Applies condition-action strategies to restrict the CGS transition matrix,
then runs CTL model checking on the pruned model. A memoryless strategy
restricts transitions based on the current state, so the matrix can be
pruned directly without tree expansion.
"""

import copy
import logging
from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.parsers.game_structures.cgs import CGS
from model_checker.utils.literals import parse_state_set_literal

logger = logging.getLogger(__name__)


def process_transition_matrix_data_fixed(
    cgs: CGS, model_path: str, agents: list[int], *strategies: dict[str, Any]
) -> list[list]:
    """Pruning with corrected state coverage logic."""
    graph = cgs.graph
    label_matrix = cgs.create_label_matrix(graph)

    for strategy_index, strategy in enumerate(strategies, start=1):
        covered_states: set[str] = set()

        for _iteration, (condition, action) in enumerate(
            strategy["condition_action_pairs"]
        ):
            # Cache model_checking results for conditions to avoid redundant CTL calls
            if not hasattr(cgs, "_condition_cache"):
                cgs._condition_cache = {}
            cache_key = (condition, model_path)
            if cache_key not in cgs._condition_cache:
                states_result = model_checking(
                    condition, model_path, preloaded_model=cgs
                )
                cgs._condition_cache[cache_key] = states_result
            else:
                states_result = cgs._condition_cache[cache_key]
            res_str = states_result.get("res", "")

            state_set: set[str] = set()
            if ": " in res_str:
                state_set = parse_state_set_literal(res_str.split(": ")[1])

            applicable_states = state_set - covered_states

            if applicable_states:
                # Apply to graph
                graph = modify_matrix(
                    graph,
                    label_matrix,
                    applicable_states,
                    action,
                    strategy_index,
                    agents,
                )
                covered_states.update(applicable_states)

        all_states = set(cgs.states)
        remaining = all_states - covered_states
        if remaining:
            graph = modify_matrix(
                graph, label_matrix, remaining, "I", strategy_index, agents
            )

    return graph


def pruning(
    cgs: CGS, model_path: str, agents: list[int], formula: str, current_agents: list
) -> bool:
    """Prune the model to a strategy profile and run CTL on the result.

    Returns True when the initial state satisfies the formula on the pruned model.
    """
    # Copy the model so the pruned graph and CTL run do not alter the shared cgs
    # used while enumerating other strategies.
    cgs1 = copy.deepcopy(cgs)
    cgs1.graph = process_transition_matrix_data_fixed(
        cgs, model_path, agents, *current_agents
    )

    # Use in-memory CTL model checking
    result = model_checking(formula, model_path, preloaded_model=cgs1)

    if "Initial state" in result.get("initial_state", "") and str(True) in result.get(
        "initial_state", ""
    ):
        return True
    return False
