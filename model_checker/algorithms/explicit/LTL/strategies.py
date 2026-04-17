"""Strategy generation for the LTL model checker.

Used when checking LTL under game-theoretic solution concepts (e.g. Nash
equilibria). Builds guarded strategies (conditions plus actions), loads
models and formulas via CGS, and delegates condition/negation generation to
the shared strategies_base module. Also provides deviation enumeration for
Nash checks and single-strategy helpers.
"""

import itertools
import logging
from typing import Dict, Generator, List, Optional, Tuple, Union

from model_checker.algorithms.explicit.shared import strategies_base
from model_checker.parsers.formulas.LTL.ltl_to_ctl import ltl_to_ctl
from model_checker.parsers.game_structures.cgs import CGS, cgs_validation

logger = logging.getLogger(__name__)


def generate_conditions(P, C, k):
    """Bridge for parameter naming compatibility."""
    return strategies_base.generate_conditions(P, C, k)


def generate_negated(input_list, max_k):
    """Bridge for parameter naming compatibility."""
    return strategies_base.generate_negated_conditions(input_list, max_k)


def generate_cartesian_products(actions_list, conditions):
    """Bridge for parameter naming compatibility."""
    return strategies_base.generate_cartesian_products(actions_list, conditions)


def generate_guarded_action_pairs(k, agent_actions, actions_list, atomic_propositions):
    """Bridge for parameter naming compatibility."""
    return strategies_base.generate_guarded_action_pairs(
        k, agent_actions, actions_list, atomic_propositions
    )


def is_duplicate(existing_dictionaries, new_dictionary):
    """Bridge for parameter naming compatibility."""
    return strategies_base.is_duplicate(existing_dictionaries, new_dictionary)


def agent_combinations(new_combinations):
    """Bridge for parameter naming compatibility."""
    return strategies_base.agent_combinations(new_combinations)


def generate_strategies(
    cartesian_products: Dict[str, List[Tuple[str, str]]],
    k: int,
    agents: List[int],
    found_solution: Union[bool, List[bool]],
) -> Generator[List[Dict], None, None]:
    """Enumerate collective strategies lazily with optional early termination.

    Builds per-agent strategy lists from cartesian_products, then yields
    each full combination via depth-first search. If ``found_solution`` is a
    list (shared mutable), stops as soon as its first element is true.
    Only combinations whose total condition complexity equals k are kept.

    Args:
        cartesian_products: Dict mapping agent keys to (condition, action) pairs.
        k: Required total complexity for a valid strategy.
        agents: Agent indices (length must match cartesian_products).
        found_solution: Boolean or single-element list; list enables early stop.

    Returns:
        Generator yielding lists of strategy dicts, one per agent (each has ``condition_action_pairs``).
    """
    strategies = [[] for _ in range(len(agents))]

    def search_solution(strategies, current_strategy, depth):
        """Enumerate strategy combinations across agents by DFS."""
        if depth == len(agents):
            yield current_strategy.copy()
        else:
            for agent in strategies[depth]:
                if isinstance(found_solution, list) and found_solution[0]:
                    return
                current_strategy.append(agent)
                yield from search_solution(strategies, current_strategy, depth + 1)
                current_strategy.pop()

    solution_found = (
        found_solution[0] if isinstance(found_solution, list) else found_solution
    )
    if not solution_found:
        for index, agent_key in enumerate(cartesian_products):
            if isinstance(found_solution, list) and found_solution[0]:
                return

            cartesian_product = cartesian_products[agent_key]
            agent_strategies = []

            for r in range(1, k + 1):
                if isinstance(found_solution, list) and found_solution[0]:
                    break

                combinations = itertools.combinations(cartesian_product, r)
                filtered_combinations = [
                    combination
                    for combination in combinations
                    if len({action for _, action in combination}) == r
                ]

                for combination in filtered_combinations:
                    if isinstance(found_solution, list) and found_solution[0]:
                        break

                    total_complexity = sum(
                        len(condition.split()) + (1 if "!" in condition else 0)
                        for condition, _ in combination
                    )
                    if total_complexity == k:
                        new_strategy = {"condition_action_pairs": list(combination)}
                        if not is_duplicate(agent_strategies, new_strategy):
                            agent_strategies.append(new_strategy)

            strategies[index] = agent_strategies

        yield from search_solution(strategies, [], 0)


def initialize(
    model_path: str, formula: str, k: int, agents: List[int]
) -> Tuple[Dict[str, List[str]], List[List[str]], List[str], str, List[int], CGS, int]:
    """Load CGS from file, convert LTL to CTL, and extract actions and propositions.

    Validates Nat idle requirements (Idle errors are ignored). Returns
    everything needed for strategy generation and model checking.

    Args:
        model_path: Path to the CGS model file.
        formula: LTL formula string.
        k: Complexity bound (logged only).
        agents: Agent indices to get actions for.

    Returns:
        Tuple of (agent_actions, actions_list, atomic_propositions, CTLformula,
        agents, cgs, num_agents). The cgs instance has filename set for pruning.

    Raises:
        FileNotFoundError: If model_path is not a file.
    """
    import os

    cgs = CGS()
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")
    cgs.read_file(filename)
    cgs.filename = filename
    logger.debug("Formula: %s", formula)

    try:
        cgs_validation.validate_nat_idle_requirements(
            cgs.graph, cgs.get_number_of_agents()
        )
    except ValueError as e:
        if "Idle error" in str(e):
            pass
        else:
            raise
    CTLformula = ltl_to_ctl(formula)
    logger.debug("Formula natATL: %s", formula)
    logger.debug("Formula CTL: %s", CTLformula)

    logger.debug("Complexity Bound: %d", k)

    actions_per_agent = cgs.get_actions(agents)
    logger.debug("Actions picked by each agent: %s", actions_per_agent)
    agent_actions = {}
    for i, key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_agent{agents[i]}"] = actions_per_agent[key]
    actions_list = list(agent_actions.values())
    atomic_propositions = cgs.get_atomic_prop()
    logger.debug("Atomic propositions: %s", atomic_propositions)

    return (
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        cgs,
        cgs.get_number_of_agents(),
    )


def generate_deviations_for_agent(
    single_strategy: Dict,
    k: int,
    agent_actions_for_agent: List[str],
    atomic_propositions: List[str],
) -> List[Dict]:
    import itertools

    C = ["and", "or"]
    conditions = list(generate_conditions(atomic_propositions, C, k))
    all_candidates = []
    for condition in conditions:
        neg_conditions = list(generate_negated([condition], k))
        all_conditions = [condition] + neg_conditions
        for cond in all_conditions:
            for action in agent_actions_for_agent:
                candidate = (cond, action)
                complexity = len(cond.split()) + (1 if "!" in cond else 0)
                if complexity <= k:
                    all_candidates.append(candidate)

    deviations = []
    current_pairs = single_strategy.get("condition_action_pairs", [])
    num_pairs = len(current_pairs)
    for candidate_tuple in itertools.product(all_candidates, repeat=num_pairs):
        candidate_strategy = {"condition_action_pairs": list(candidate_tuple)}
        if candidate_strategy != single_strategy:
            total_complexity = sum(
                len(pair[0].split()) + (1 if "!" in pair[0] else 0)
                for pair in candidate_tuple
            )
            if total_complexity <= k:
                deviations.append(candidate_strategy)
    return deviations


def generate_single_strategy(
    selected_agents: List[int],
    k: int,
    agent_actions: Dict[str, List[str]],
    actions_list: List[List[str]],
    atomic_propositions: List[str],
) -> Optional[List[Dict]]:
    """Return the first collective strategy for selected_agents with total complexity k.

    Builds guarded action pairs, then runs the strategy generator and
    returns the first yielded strategy, or None if there are none.

    Args:
        selected_agents: Agent indices.
        k: Target total complexity.
        agent_actions: Per-agent action sets.
        actions_list: List of action lists per agent.
        atomic_propositions: Model propositions.

    Returns:
        One list of strategy dicts (one per agent), or None.
    """
    found_solution = False
    cartesian_products = generate_guarded_action_pairs(
        k, agent_actions, actions_list, atomic_propositions
    )
    strategy_generator = generate_strategies(
        cartesian_products, k, selected_agents, found_solution
    )
    try:
        return next(strategy_generator)
    except StopIteration:
        return None


def generate_single_strategy_random(
    selected_agents: List[int],
    k: int,
    agent_actions: Dict[str, List[str]],
    atomic_propositions: List[str],
) -> Optional[List[Dict]]:
    """Build one collective strategy by taking the first (condition, action) per agent.

    For each agent, takes the first pair from the sorted guarded-action list
    (deterministic). Returns a strategy only if the sum of condition
    complexities equals k (complexity = token count + 1 if ``"!"`` in condition).
    Tries up to 100 times; if no valid strategy is found, returns None.

    Args:
        selected_agents: Agent indices.
        k: Target total complexity.
        agent_actions: Per-agent action sets (keys e.g. ``"agent{i}"``).
        atomic_propositions: Proposition names for condition generation.

    Returns:
        List of one strategy dict per agent (each with one pair), or None.
    """
    actions_list = [agent_actions.get(f"agent{agent}", []) for agent in selected_agents]
    cartesian_products = generate_guarded_action_pairs(
        k, agent_actions, actions_list, atomic_propositions
    )
    attempts = 100
    for _ in range(attempts):
        strategy = []
        total_complexity = 0
        valid = True
        for agent in selected_agents:
            key = f"actions_agent{agent}"
            candidate_list = cartesian_products.get(key, [])
            if not candidate_list:
                valid = False
                break
            candidate_list_sorted = sorted(candidate_list)
            cond, act = candidate_list_sorted[0]
            strategy.append((cond, act))
            cplx = len(cond.split())
            if "!" in cond:
                cplx += 1
            total_complexity += cplx
        if valid and total_complexity == k:
            return [{"condition_action_pairs": [(s[0], s[1])]} for s in strategy]
    return None
