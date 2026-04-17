"""LTL model checking with game-theoretic solution concepts.

This module provides LTL model checking extended with game-theoretic notions:
sure-win strategies (coalition can force the formula to hold), Nash equilibria,
and checks for "win/lose in some Nash". Formulas are converted to CTL and
evaluated on the model; strategies are enumerated by complexity and the
model is pruned under each strategy before verification.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from model_checker.algorithms.explicit.LTL.pruning import pruning
from model_checker.algorithms.explicit.LTL.strategies import (
    generate_guarded_action_pairs,
    generate_strategies,
    initialize,
)
from model_checker.algorithms.explicit.SolutionConcepts.Solution_Concepts import (
    exists_nash,
    is_not_nash,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol

logger = logging.getLogger(__name__)

LTL_KEYWORDS = {
    "x",
    "f",
    "g",
    "u",
    "and",
    "or",
    "not",
    "next",
    "eventually",
    "globally",
    "until",
    "implies",
    "true",
    "false",
}


def _validate_ltl_input(
    formula: str, filename: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Check that formula and filename are non-empty.

    Returns:
        An error dict if validation fails, otherwise None.
    """
    from model_checker.utils.error_handler import create_validation_error

    if not formula or not formula.strip():
        return create_validation_error("Formula not entered")
    if not filename:
        return create_validation_error("Model file not specified")
    return None


def _parse_ltl_formula(formula: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """Parse LTL formula. Returns (parsed, None) or (None, error_dict)."""
    from model_checker.parsers.formula_parser_factory import (
        FormulaParserFactory,
    )
    from model_checker.utils.error_handler import create_syntax_error

    parser = FormulaParserFactory.get_parser_instance("LTL")
    parsed = parser.parse(formula)
    if parsed is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in LTL formula"
        return None, create_syntax_error(error_msg)
    return parsed, None


def _load_ltl_model(filename: str) -> Any:
    """Load the CGS model from the given file for LTL model checking."""
    from model_checker.models.model_factory import (
        create_model_parser_for_logic,
    )

    cgs = create_model_parser_for_logic(filename, "LTL")
    cgs.read_file(filename)
    return cgs


def _validate_formula_propositions(
    formula: str, atomic_propositions: List[str]
) -> Optional[Dict[str, Any]]:
    """Ensure every proposition used in the formula is declared in the model.

    Returns:
        An error dict if any proposition is missing, otherwise None.
    """
    from model_checker.utils.error_handler import create_validation_error

    formula_props = set(re.findall(r"\b([a-z]+)\b", formula)) - LTL_KEYWORDS
    invalid = formula_props - set(atomic_propositions)
    if invalid:
        return create_validation_error(
            f"Atomic proposition(s) {', '.join(sorted(invalid))} "
            f"do not exist in the model"
        )
    return None


def _run_sure_win_and_format_result(
    filename: str,
    formula: str,
    k: int,
    agents: List[int],
    cgs: CGSProtocol,
) -> Dict[str, Any]:
    """Run sure-win check and return the standard result dict with ``res`` and ``initial_state``."""
    initial_state = cgs.get_initial_state()
    result = model_checking_sure_win(filename, formula, k, agents)
    if result.get("Satisfiability"):
        return {
            "res": "Result: {satisfied}",
            "initial_state": f"Initial state {initial_state}: True",
        }
    return {
        "res": "Result: {}",
        "initial_state": f"Initial state {initial_state}: False",
    }


def model_checking_sure_win(
    model: Any, formula: str, k: int, agents: List[int]
) -> Dict[str, Any]:
    """Decide whether the coalition has a sure-win strategy for the formula.

    Searches for a strategy that makes the formula hold in every outcome.
    Strategies are enumerated by complexity (1 to k); for each candidate,
    the model is pruned under that strategy and the formula is checked (via
    CTL). The first satisfying strategy is returned.

    Args:
        model: Path to the model file.
        formula: LTL formula string.
        k: Maximum strategy complexity bound.
        agents: Agent indices in the coalition.

    Returns:
        Dict with keys ``Satisfiability`` (bool) and ``Complexity Bound`` (int).
    """
    result = {}
    found_solution = False
    (
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        cgs,
        _nash_agents,
    ) = initialize(model, formula, k, agents)
    i = 1

    found_solution_state = [False]

    while not found_solution_state[0] and i <= k:
        cartesian_products = generate_guarded_action_pairs(
            i, agent_actions, actions_list, atomic_propositions
        )
        strategies_generator = generate_strategies(
            cartesian_products, i, agents, found_solution_state
        )

        for current_strategy in strategies_generator:
            if found_solution_state[0]:
                break

            found_solution = pruning(cgs, model, agents, CTLformula, current_strategy)
            if found_solution:
                found_solution_state[0] = True
                found_solution = True
                logger.info("Solution found! It is not a Nash Equilibrium!")
                logger.info("Satisfiable formula")
                result["Satisfiability"] = found_solution
                result["Complexity Bound"] = i
                break

        if found_solution_state[0]:
            break
        i += 1
    else:
        if not found_solution_state[0]:
            logger.info(
                "Formula does not satisfy the given model, "
                "the game brings to a Nash Equilibrium for the selected agents"
            )
            logger.info("Unsatisfiable formula")
            result["Satisfiability"] = False
            result["Complexity Bound"] = k

    return result


def model_checking_is_not_nash(
    model: Any,
    cgs: CGSProtocol,
    formula: str,
    k: int,
    natural_strategies: Any,
    selected_agents: List[int],
) -> Dict[str, Any]:
    """Check whether the given strategy profile is not a Nash equilibrium.

    If any agent can improve by unilaterally deviating from natural_strategies,
    the profile is not Nash and Satisfiability is set to False.

    Args:
        model: Path to the model file.
        cgs: Pre-loaded CGS model.
        formula: LTL formula string.
        k: Complexity bound for strategies.
        natural_strategies: Strategy profile to test.
        selected_agents: Agent indices to consider for deviations.

    Returns:
        Dict with ``Satisfiability`` (False if not Nash, True if Nash) and ``Complexity Bound``.
    """
    result = {}

    (
        agent_actions,
        _actions_list,
        atomic_propositions,
        CTLformula,
        _agents,
        _filename,
        _nash_agents,
    ) = initialize(model, formula, k, selected_agents)

    logger.debug("Natural strategies created: %s", natural_strategies)

    if natural_strategies is not None:
        logger.debug("Using manually provided natural strategies.")

        if is_not_nash(
            model,
            cgs,
            selected_agents,
            CTLformula,
            natural_strategies,
            k,
            agent_actions,
            atomic_propositions,
        ):
            logger.info(
                "Deviation found: the natural strategy is NOT a Nash Equilibrium!"
            )
            result["Satisfiability"] = False
            result["Complexity Bound"] = k
            return result
        else:
            logger.info(
                "No deviation found: the natural strategy "
                "appears to be a Nash Equilibrium!"
            )
            result["Satisfiability"] = True
            result["Complexity Bound"] = k
            return result


def model_checking_exists_nash(
    model: Any, formula: str, k: int, agents: List[int]
) -> Dict[str, Any]:
    """Decide whether some Nash equilibrium exists for the formula and agents.

    Enumerates strategy profiles by complexity (1 to k) and returns as soon
    as a profile is found where no agent can profitably deviate.

    Args:
        model: Path to the model file.
        formula: LTL formula string.
        k: Maximum strategy complexity bound.
        agents: Agent indices to consider.

    Returns:
        Dict with ``Satisfiability`` and ``Complexity Bound``.
    """
    (
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        cgs,
        nash_agents,
    ) = initialize(model, formula, k, agents)

    found_solution = [False]
    result = {}

    for i in range(1, k + 1):
        cartesian_products = generate_guarded_action_pairs(
            i, agent_actions, actions_list, atomic_propositions
        )
        strategies_generator = generate_strategies(
            cartesian_products, i, agents, found_solution
        )

        for current_strategy in strategies_generator:
            if exists_nash(
                cgs,
                list(range(1, nash_agents + 1)),
                CTLformula,
                current_strategy,
                i,
                agent_actions,
                atomic_propositions,
            ):
                logger.info("Nash Equilibrium found!")
                found_solution[0] = True
                result["Satisfiability"] = True
                result["Complexity Bound"] = i
                return result

    logger.info("The game doesn't lead to a Nash Equilibrium for the selected agents")
    result["Satisfiability"] = False
    result["Complexity Bound"] = k
    return result


def model_checking_wins_some_nash(
    cgs: CGSProtocol,
    model: str,
    agents: List[int],
    CTLformula: Any,
    current_strategy: Any,
    bound: int,
    agent_actions: Any,
    atomic_propositions: Any,
    target_agent: int,
) -> Dict[str, Any]:
    """Check whether target_agent wins in the given strategy profile when it is Nash.

    Verifies that the path induced by current_strategy satisfies target_agent's
    objective and that the profile is a Nash equilibrium (no profitable deviation).
    If both hold, the result indicates the agent wins in this Nash.

    Args:
        cgs: CGS model instance.
        model: Path to the model file (used by pruning for cache and CTL).
        agents: All agent indices.
        CTLformula: CTL encoding of the objective.
        current_strategy: Strategy profile to evaluate.
        bound: Strategy complexity bound.
        agent_actions: Per-agent action sets.
        atomic_propositions: Model atomic propositions.
        target_agent: Agent index whose winning is checked.

    Returns:
        Dict with ``Satisfiability`` (True if agent wins in this Nash).
    """
    result = {}

    if check_agent_win(
        cgs, model, target_agent, CTLformula, current_strategy
    ) and not is_not_nash(
        model,
        cgs,
        agents,
        CTLformula,
        current_strategy,
        bound,
        agent_actions,
        atomic_propositions,
    ):
        result["Satisfiability"] = False
        return result

    result["Satisfiability"] = True
    return result


def check_agent_win(
    cgs: CGSProtocol,
    model: str,
    agent: int,
    CTLformula: Any,
    current_strategy: Any,
) -> bool:
    """Check whether the agent's objective holds under the given strategy.

    Prunes the model with the strategy and runs CTL model checking for
    the agent's formula on the pruned model.

    Args:
        cgs: CGS model instance.
        model: Path to the model file (used by pruning for cache and CTL).
        agent: Agent index.
        CTLformula: Agent objective (CTL formula).
        current_strategy: Strategy profile to evaluate.

    Returns:
        True if the objective is satisfied, False otherwise.
    """
    return pruning(cgs, model, [agent], CTLformula, current_strategy)


def model_checking_lose_some_nash(
    cgs: CGSProtocol,
    model: str,
    agents: List[int],
    CTLformula: Any,
    current_strategy: Any,
    bound: int,
    agent_actions: Any,
    atomic_propositions: Any,
    target_agent: int,
) -> Dict[str, Any]:
    """Check whether target_agent loses in the given profile when it is Nash.

    Dual of wins_some_nash: the agent's objective fails on the induced path
    and the profile is a Nash equilibrium.

    Args:
        cgs: CGS model instance.
        model: Path to the model file (used by pruning for cache and CTL).
        agents: All agent indices.
        CTLformula: CTL encoding of the objective.
        current_strategy: Strategy profile to evaluate.
        bound: Strategy complexity bound.
        agent_actions: Per-agent action sets.
        atomic_propositions: Model atomic propositions.
        target_agent: Agent index whose loss is checked.

    Returns:
        Dict with ``Satisfiability`` (True if agent loses in this Nash).
    """
    result = {}

    if not check_agent_win(
        cgs, model, target_agent, CTLformula, current_strategy
    ) and not is_not_nash(
        model,
        cgs,
        agents,
        CTLformula,
        current_strategy,
        bound,
        agent_actions,
        atomic_propositions,
    ):
        result["Satisfiability"] = True
        return result

    result["Satisfiability"] = False
    return result


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Main entry point for LTL model checking (sure-win, standard API).

    Validates input, clears caches, loads the model, and runs sure-win
    checking with k=5 and all agents. The formula is converted to CTL
    for verification.

    Args:
        formula: LTL formula string.
        filename: Path to the model file.

    Returns:
        Dict with ``res`` and ``initial_state`` (and optionally ``error``).
    """
    from model_checker.utils.error_handler import (
        create_model_error,
        create_system_error,
    )

    err = _validate_ltl_input(formula, filename)
    if err is not None:
        return err

    try:
        _, parse_err = _parse_ltl_formula(formula)
        if parse_err is not None:
            return parse_err

        cgs = _load_ltl_model(filename)
        atomic_propositions = cgs.get_atomic_prop()
        prop_err = _validate_formula_propositions(formula, atomic_propositions)
        if prop_err is not None:
            return prop_err

        k = 5
        agents = list(range(1, cgs.get_number_of_agents() + 1))
        return _run_sure_win_and_format_result(filename, formula, k, agents, cgs)

    except FileNotFoundError:
        return create_system_error(f"Model file not found: {filename}")
    except ValueError as e:
        error_msg = str(e)
        if "index" in error_msg.lower() or "dimension" in error_msg.lower():
            return create_model_error(error_msg)
        return create_system_error(error_msg)
    except Exception as e:
        return create_system_error(f"Error during model checking: {str(e)}")
