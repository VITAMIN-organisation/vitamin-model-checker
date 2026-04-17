"""
PrefilterATL optimization for NatATL Recall verification.

This module provides a performance optimization by first checking if the
formula is satisfied as standard ATL (ignoring complexity bounds). If ATL
fails, NatATL must also fail, so we can return early without running the
expensive NatATL verification.
"""

import logging
import os
import time
from typing import Any, Dict

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_model_checking,
)
from model_checker.algorithms.explicit.NatATL.NatATLtoATL import (
    natatl_to_atl,
)
from model_checker.algorithms.explicit.NatATL.Recall.solver import (
    solve_natatl_recall,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_initialization import (  # noqa: E501
    initialize,
)
from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

logger = logging.getLogger(__name__)


def preprocess_and_verify(model: str, formula: str) -> Dict[str, Any]:
    """
    Prefilter optimization: check ATL first, then NatATL if needed.

    This function implements a performance optimization:
    1. Convert NatATL formula to ATL (removes complexity bounds)
    2. Check if ATL formula is satisfied (fast check)
    3. If ATL fails, NatATL must also fail (early return)
    4. If ATL succeeds, run full NatATL verification to find bounded strategy

    Args:
        model: Path to model file
        formula: NatATL formula string

    Returns:
        Dictionary with verification result
    """
    start_time = time.time()
    res: Dict[str, Any] = {}

    if not os.path.isfile(model):
        raise FileNotFoundError(f"No such file or directory: {model}")

    logger.debug("NatATL formula: %s", formula)

    # Convert NatATL to ATL (removes complexity bounds)
    atlformula = natatl_to_atl(formula)
    logger.debug("Converted ATL formula: %s", atlformula)

    # Create model parser
    cgs = create_model_parser_for_logic(model, "NatATL_Recall")
    cgs.read_file(model)

    # Parse ATL formula for validation
    res_parsing = FormulaParserFactory.parse_formula(
        "ATL", atlformula, n_agent=cgs.get_number_of_agents()
    )
    logger.debug("ATL parsing result: %s", res_parsing)

    # Fast ATL check
    result = atl_model_checking(atlformula, model)
    logger.debug("ATL verification result: %s", result)

    if result.get("initial_state") == f"Initial state {cgs.initial_state}: True":
        logger.info("ATL satisfied, proceeding with NatATL verification")
        res = _run_natatl_recall(model, formula)
    else:
        logger.info("ATL not satisfied, NatATL must also fail (early termination)")
        res["Satisfiability"] = False
        res["Complexity Bound"] = None

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info("Total verification time: %.3f seconds", elapsed_time)

    return res


def _run_natatl_recall(model: str, formula: str) -> Dict[str, Any]:
    """
    Execute NatATL Recall verification (called after ATL prefilter succeeds).

    This function runs the full NatATL verification using the solver module.
    It's called by preprocess_and_verify after confirming ATL is satisfied.

    Args:
        model: Path to model file
        formula: NatATL formula string

    Returns:
        Dictionary with Satisfiability, Complexity Bound, and Winning Strategy
    """
    # Initialize model and parse formula
    (
        k,
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        filename,
        model_parser,
    ) = initialize(model, formula)

    # Solve using the solver module
    result = solve_natatl_recall(
        k,
        agent_actions,
        actions_list,
        atomic_propositions,
        CTLformula,
        agents,
        model_parser,
        filename,
    )

    return result
