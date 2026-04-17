"""
Combined ATL and NatATL Verification Pipeline.

This module provides a heuristic optimization to speed up verification:
1. First, check the formula as standard ATL (ignoring complexity bounds).
2. If ATL is satisfied, attempt NatATL verification to find a bounded strategy.
3. If ATL fails, NatATL must also fail (since NatATL <= ATL), so return early.
"""

import logging
import os
import time
from typing import Any, Dict

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_model_checking,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.solver import (
    solve_natatl_memoryless,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.strategies import (
    initialize,
)
from model_checker.algorithms.explicit.NatATL.NatATLtoATL import (
    natatl_to_atl,
)
from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import CGSProtocol
from model_checker.utils.error_handler import create_system_error

logger = logging.getLogger(__name__)


def preprocess_and_verify(model_path: str, formula: str) -> Dict[str, Any]:
    """
    Run ATL pre-check followed by NatATL verification if promising.

    Args:
        model_path: Path to model file
        formula: NatATL formula string

    Returns:
        Verification result dictionary
    """
    start_time = time.time()

    if not os.path.isfile(model_path):
        return create_system_error(f"Model file not found: {model_path}")

    atlformula = natatl_to_atl(formula)
    logger.debug("Checking optimistic ATL formula: %s", atlformula)

    try:
        cgs = create_model_parser_for_logic(model_path, "NatATL")
        cgs.read_file(model_path)

        # Parse formula to validate
        FormulaParserFactory.parse_formula(
            "ATL", atlformula, n_agent=cgs.get_number_of_agents()
        )

        atl_result = atl_model_checking(atlformula, model_path)
        logger.debug("ATL Pre-check result: %s", atl_result)

        result: Dict[str, Any] = {}

        initial_state_res = atl_result.get("initial_state", "")

        if "True" in initial_state_res:
            logger.info("ATL pre-check passed. Proceeding to NatATL verification.")
            result = process_data(cgs, model_path, formula)
        else:
            logger.info("ATL pre-check failed. Formula unstatisfiable in NatATL.")
            result["Satisfiability"] = False
            result["res"] = "Result: False"
            result["initial_state"] = f"Initial state {cgs.initial_state}: False"

        elapsed_time = time.time() - start_time
        logger.info("Total verification time: %.3f seconds", elapsed_time)

        return result

    except Exception as e:
        logger.exception("Error during pre-filtered verification")
        return create_system_error(f"Error: {str(e)}")


def process_data(cgs: CGSProtocol, model_path: str, formula: str) -> Dict[str, Any]:
    """
    Execute NatATL verification loop.

    Args:
        cgs: CGS Object for pre-check
        model_path: Path to model file
        formula: NatATL formula string
    """
    # Pass the existing CGS object to avoid re-reading the model file
    (
        k,
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        cgs_init,
    ) = initialize(model_path, formula, cgs=cgs)

    # Use the shared solver module to avoid duplication
    result = solve_natatl_memoryless(
        k,
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        cgs_init,
        model_path,
    )

    return result
