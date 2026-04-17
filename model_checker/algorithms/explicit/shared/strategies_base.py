"""Strategy generation for NatATL-style model checkers.

Used by NatATL (memoryless), NatATLF, and NatSL to build guarded strategies:
conditions over atomic propositions paired with actions, enumerated up to a
complexity bound. Provides condition generation, negation expansion, cartesian
products of conditions and actions, and lazy strategy enumeration so all
checkers share one implementation.
"""

import itertools
import logging
from typing import Dict, Generator, List, Set, Tuple

logger = logging.getLogger(__name__)


def generate_conditions(
    atomic_props: List[str], connectives: List[str], max_complexity: int
) -> Generator[str, None, None]:
    """Enumerate boolean conditions over atoms up to a token-complexity limit.

    Builds conditions recursively by combining atomic propositions with the
    given connectives (e.g. "and", "or"). Complexity is the number of
    space-separated tokens; only conditions with complexity <= max_complexity
    are yielded. Connective choice is deterministic so the same inputs give
    the same outputs across runs.

    Args:
        atomic_props: Proposition names (e.g. ``['a', 'b', 'c']``).
        connectives: Connective operators (e.g. ``['and', 'or']``); first is used.
        max_complexity: Maximum number of tokens per condition.

    Returns:
        Generator yielding condition strings such as ``"a"``, ``"a && b"``, ``"a and b or c"``.
    """
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
    """Expand conditions into all variants with some atoms negated.

    For each condition (e.g. ``"a && b"``), yields every combination of
    negating or not negating each atom: ``"!a && b"``, ``"a && !b"``,
    ``"!a && !b"``. Only variants whose complexity (token count + 1 per ``!``)
    is at most max_complexity are yielded.

    Args:
        conditions: Condition strings to expand (atoms joined by ``" && "``).
        max_complexity: Maximum allowed complexity for a yielded string.

    Returns:
        Generator yielding negated condition strings within the complexity bound.
    """
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
    """Enumerate collective strategies (one (condition, action) mapping per agent).

    Each yielded item is a list of strategy dicts, one per agent, where each
    dict has key ``"condition_action_pairs"`` with a list of (condition, action)
    tuples. Only combinations whose total condition complexity equals
    complexity_bound are considered. Enumeration is lazy (depth-first) to avoid
    blowing up memory on large strategy spaces.

    Args:
        cartesian_products: Per-agent lists of (condition, action) pairs.
        complexity_bound: Required total complexity for a valid strategy.
        agents: Agent indices (length must match cartesian_products usage).
        found_solution: If True, nothing is yielded (used for early termination).

    Returns:
        Generator yielding lists of strategy dicts, one dict per agent.
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
    """
    Check if a strategy already exists in the list.

    Prevents duplicate strategies from being generated multiple times,
    which would waste computation during model checking.

    Args:
        existing_strategies: List of previously generated strategies
        new_strategy: New strategy to check for duplicates

    Returns:
        True if new_strategy matches an existing one, False otherwise
    """
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
    """Build all (condition, action) pairs per agent.

    For each agent index i, takes actions_list[i] and forms the product with
    conditions, giving every (cond, act) pair that agent could use in a
    guarded strategy.

    Args:
        actions_list: One list of action names per agent.
        conditions: Condition strings to pair with actions.

    Returns:
        Dict from keys ``"actions_agent1"``, ``"actions_agent2"``, ... to
        lists of ``(condition, action)`` tuples.
    """
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
    """Produce all (condition, action) pairs for each agent up to a complexity bound.

    Main entry point for strategy generation: builds conditions from
    atomic_propositions and connectives, expands with negation variants, then
    pairs every resulting condition with every action for each agent. Used by
    NatATL-family checkers to feed strategy enumeration.

    Args:
        complexity_bound: Max condition complexity (typically the formula's k).
        agent_actions: Map from agent keys (e.g. ``"agent1"``) to action lists.
        actions_list: List of action lists, one per agent, in same order as agents.
        atomic_propositions: Proposition names available in the model.

    Returns:
        Map from keys like ``"actions_agent1"`` to lists of ``(condition, action)``.
        On error returns an empty dict and logs.
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
    """Yield every pair (a, b) with a and b from new_combinations.

    Used when building or comparing strategies across two agent combinations.

    Args:
        new_combinations: Iterable of agent or combination identifiers.

    Returns:
        Generator yielding pairs ``(a, b)`` for each a, b in new_combinations.
    """
    for agent1 in new_combinations:
        for agent2 in new_combinations:
            yield agent1, agent2
