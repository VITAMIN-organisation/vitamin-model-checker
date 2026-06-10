"""Generate guarded strategies (condition-action pairs) for NatATL-style checkers."""

import itertools
import logging
from typing import Dict, Generator, List, Set, Tuple

logger = logging.getLogger(__name__)


def generate_conditions(
    atomic_props: List[str], connectives: List[str], max_complexity: int
) -> Generator[str, None, None]:
    """Yield boolean conditions over atoms up to a given token count."""
    condition_set: Set[str] = set()

    def generate_condition(k: int, condition: List[str]) -> Generator[str, None, None]:
        if k == 0:
            condition_str = " && ".join(condition)
            if condition_str not in condition_set:
                yield condition_str
                condition_set.add(condition_str)
        else:
            for p in atomic_props:
                if p not in condition:
                    new_condition = condition + [p]
                    if len(new_condition) == 1:
                        yield from generate_condition(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        new_condition.sort()
                        connective = connectives[0] if connectives else "and"
                        new_condition_str = new_condition[0] + " " + connective + " "
                        for i in range(1, len(new_condition) - 1):
                            new_condition_str += (
                                new_condition[i] + " " + connective + " "
                            )
                        new_condition_str += new_condition[-1]
                        complexity = len(new_condition_str.split())
                        if complexity <= max_complexity:
                            yield from generate_condition(k - 1, [new_condition_str])

    for k in range(1, max_complexity + 1):
        yield from generate_condition(k, [])


def generate_negated_conditions(
    conditions: List[str], max_complexity: int
) -> Generator[str, None, None]:
    """Yield each condition with every choice of negated atoms, within max_complexity."""
    for condition in conditions:
        atomic_props = condition.split(" && ")
        for combo in itertools.product(["", "!"], repeat=len(atomic_props)):
            negated_props = [
                f"{combo[i]}{atomic_props[i]}" for i in range(len(atomic_props))
            ]
            new_str = " && ".join(negated_props)
            complexity = len(new_str.split())
            if "!" in new_str:
                complexity += 1
            if complexity <= max_complexity:
                yield new_str


def generate_strategies(
    cartesian_products: Dict[str, List[Tuple[str, str]]],
    complexity_bound: int,
    agents: List[int],
    found_solution: bool,
) -> Generator[List[Dict], None, None]:
    """Yield strategy profiles (one guarded mapping per agent) at complexity_bound.

    Stops yielding when found_solution is True.
    """
    strategies = [[] for _ in range(len(agents))]

    def search_solution(
        strategies: List[List[Dict]],
        current_strategy: List[Dict],
        depth: int,
    ) -> Generator[List[Dict], None, None]:
        """Enumerate collective strategies by depth-first combination over agents."""
        if depth == len(agents):
            yield current_strategy
        else:
            for agent in strategies[depth]:
                current_strategy.append(agent)
                yield from search_solution(strategies, current_strategy, depth + 1)
                current_strategy.pop()

    if not found_solution:
        for index, agent_key in enumerate(cartesian_products):
            cartesian_product = cartesian_products[agent_key]

            for r in range(1, complexity_bound + 1):
                combinations = itertools.combinations(cartesian_product, r)
                filtered_combinations = [
                    combination
                    for combination in combinations
                    if len({action for _, action in combination}) == r
                ]
                for combination in filtered_combinations:
                    total_complexity = sum(
                        len(condition.split()) + (1 if "!" in condition else 0)
                        for condition, _ in combination
                    )
                    if total_complexity == complexity_bound:
                        new_strategy = {"condition_action_pairs": list(combination)}
                        if not is_duplicate(strategies[index], new_strategy):
                            strategies[index].append(new_strategy)
                            yield from search_solution(strategies, [], 0)


def is_duplicate(existing_strategies: List[Dict], new_strategy: Dict) -> bool:
    """Return True if new_strategy has the same condition_action_pairs as one already listed."""
    for existing_strategy in existing_strategies:
        if (
            existing_strategy["condition_action_pairs"]
            == new_strategy["condition_action_pairs"]
        ):
            return True
    return False


def generate_cartesian_products(
    actions_list: List[List[str]], conditions: List[str]
) -> Dict[str, List[Tuple[str, str]]]:
    """Pair every condition with every action for each agent (actions_agent1, ...)."""
    cartesian_products = {}
    for i, actions in enumerate(actions_list, start=1):
        agent_key = f"actions_agent{i}"
        agent_cartesian_product = list(itertools.product(conditions, actions))
        if agent_key not in cartesian_products:
            cartesian_products[agent_key] = []
        cartesian_products[agent_key].extend(agent_cartesian_product)
    return cartesian_products


def generate_guarded_action_pairs(
    complexity_bound: int,
    agent_actions: Dict[str, List[str]],
    actions_list: List[List[str]],
    atomic_propositions: List[str],
) -> Dict[str, List[Tuple[str, str]]]:
    """Build all (condition, action) pairs per agent up to complexity_bound.

    Returns an empty dict on error.
    """
    connectives = ["and", "or"]
    try:
        cartesian_products: Dict[str, List[Tuple[str, str]]] = {}
        for _agent_key in agent_actions.keys():
            conditions = list(
                generate_conditions(atomic_propositions, connectives, complexity_bound)
            )
            for condition in conditions:
                negated_conditions = list(
                    generate_negated_conditions([condition], complexity_bound)
                )
                all_conditions = [condition] + negated_conditions
                new_cartesian_products = generate_cartesian_products(
                    actions_list, all_conditions
                )
                for key, value in new_cartesian_products.items():
                    if key not in cartesian_products:
                        cartesian_products[key] = []
                    cartesian_products[key].extend(value)
        return cartesian_products

    except Exception as e:
        logger.error("Error generating guarded action pairs: %s", e)
        return {}


def agent_combinations(new_combinations: List) -> Generator[Tuple, None, None]:
    """Yield all ordered pairs from new_combinations."""
    for agent1 in new_combinations:
        for agent2 in new_combinations:
            yield agent1, agent2
