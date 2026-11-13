"""Rule-by-rule matrix pruning for the LTL solution concepts: each condition-action
rule cuts the CGS transition matrix in the states where it matches first."""

from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    states_of_result,
)
from model_checker.parsers.game_structures.cgs import CGS


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
