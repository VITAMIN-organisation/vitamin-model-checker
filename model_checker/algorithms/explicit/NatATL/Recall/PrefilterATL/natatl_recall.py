"""NatATL Recall entry point."""

import logging
import os
import time
from typing import Any

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


def preprocess_and_verify(model: str, formula: str) -> dict[str, Any]:
    """ATL parse-check (bounds stripped), then full recall verification."""
    start_time = time.time()
    res: dict[str, Any] = {}

    if not os.path.isfile(model):
        raise FileNotFoundError(f"No such file or directory: {model}")

    logger.debug("NatATL formula: %s", formula)

    # Convert NatATL to ATL (removes complexity bounds)
    atlformula = natatl_to_atl(formula)
    logger.debug("Converted ATL formula: %s", atlformula)

    # Create model parser
    cgs = create_model_parser_for_logic(model, "NatATL_Recall")
    cgs.read_file(model)

    # Parse ATL surface syntax only (bounds already stripped); no ATL model check.
    res_parsing = FormulaParserFactory.parse_formula(
        "ATL", atlformula, n_agent=cgs.get_number_of_agents()
    )
    logger.debug("ATL parsing result: %s", res_parsing)

    res = _run_natatl_recall(model, formula)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info("Total verification time: %.3f seconds", elapsed_time)

    return res


def _run_natatl_recall(model: str, formula: str) -> dict[str, Any]:
    """Initialize and call ``solve_natatl_recall``."""
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
