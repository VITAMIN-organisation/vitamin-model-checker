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
    generate_strategies,
    initialize,
)
from model_checker.algorithms.explicit.shared import strategies_base
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
    """Return an error dict if formula or filename is missing; otherwise None."""
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
    """Return an error dict if the formula uses undeclared propositions; otherwise None."""
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
    initial_state = cgs.initial_state
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
    """Search for a sure-win strategy up to complexity k.

    Returns Satisfiability and the complexity bound where a strategy was found.
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
        cartesian_products = strategies_base.generate_guarded_action_pairs(
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
    """Test whether natural_strategies is Nash.

    Satisfiability is False if some agent can improve by deviating alone.
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
    """Search for a Nash equilibrium up to complexity k."""
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
        cartesian_products = strategies_base.generate_guarded_action_pairs(
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
    """Test one strategy profile for a single agent.

    Satisfiability is False when the target agent meets the CTL goal on the play
    from this strategy and no agent can improve by deviating alone (Nash).
    Otherwise Satisfiability is True.
    """
    result = {}

    if pruning(
        cgs, model, [target_agent], CTLformula, current_strategy
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
    """Test one strategy profile for a single agent (lose case).

    Satisfiability is True when the target agent misses the CTL goal and the
    profile is Nash. Otherwise Satisfiability is False.
    """
    result = {}

    if not pruning(
        cgs, model, [target_agent], CTLformula, current_strategy
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
    """Main entry point for LTL sure-win checking (k=5, all agents)."""
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
        atomic_propositions = cgs.atomic_propositions
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
