"""
Recall strategy generation for NatATL.

Lazy enumeration of collective strategies with duplicate detection.
"""

import logging
from collections.abc import Generator
from itertools import combinations, product

logger = logging.getLogger(__name__)


def generate_strategies(
    cartesian_products: dict[str, list[tuple[str, str]]],
    complexity_bound: int,
    agents: list[int],
    found_solution: bool,
) -> Generator[list[dict], None, None]:
    """
    Generate collective strategies for all agents via lazy enumeration.

    Each strategy maps conditions (including regex) to actions. Uses depth-first
    search to enumerate combinations without memory explosion.
    """
    logger.debug("Generating strategies...")
    strategies = [[] for _ in range(len(agents))]

    def search_solution(
        strategies: list[list[dict]],
        current_strategy: list[dict],
        depth: int,
    ) -> Generator[list[dict], None, None]:
        """Recursively enumerate all collective strategy combinations."""
        if depth == len(agents):
            yield list(current_strategy)
        else:
            for agent_strategy in strategies[depth]:
                current_strategy.append(agent_strategy)
                yield from search_solution(strategies, current_strategy, depth + 1)
                current_strategy.pop()

    if not found_solution:
        for index, agent_key in enumerate(cartesian_products):
            cartesian_product = cartesian_products[agent_key]

            for r in range(1, complexity_bound + 1):
                combinations_iter = combinations(cartesian_product, r)
                filtered_combinations = [
                    combination
                    for combination in combinations_iter
                    if len({action for _, action in combination}) == r
                ]
                for combination in filtered_combinations:
                    total_complexity = sum(
                        len(str(condition).split())
                        + (1 if "!" in str(condition) or "*" in str(condition) else 0)
                        for condition, _ in combination
                    )
                    if total_complexity == complexity_bound:
                        new_strategy = {"condition_action_pairs": list(combination)}
                        if not is_duplicate(strategies[index], new_strategy):
                            strategies[index].append(new_strategy)

        return search_solution(strategies, [], 0)
    else:
        return


def is_duplicate(existing_strategies: list[dict], new_strategy: dict) -> bool:
    """Check if strategy already exists to prevent duplicates."""
    for existing_strategy in existing_strategies:
        if (
            "condition_action_pairs" in existing_strategy
            and existing_strategy["condition_action_pairs"]
            == new_strategy["condition_action_pairs"]
        ):
            return True
    return False


def generate_guarded_action_pairs(
    regex_list: list[str], agent_actions: list[list[str]]
) -> dict[str, list[tuple[str, str]]]:
    """
    Generate cartesian product of regex conditions and actions per agent.

    Args:
        regex_list: List of regex pattern strings
        agent_actions: List of action sets, one per agent

    Returns:
        Dict mapping agent keys to lists of (regex, action) pairs
    """
    result = {}
    for i, actions in enumerate(agent_actions):
        agent_key = f"actions_agent{i + 1}"
        cartesian_product = list(product(regex_list, actions))
        result[agent_key] = cartesian_product
    return result
