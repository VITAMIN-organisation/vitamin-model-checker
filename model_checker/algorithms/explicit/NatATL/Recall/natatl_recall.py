"""NatATL model checker with recall strategies: rules whose conditions are patterns
over the history, each profile checked with CTL on the model restricted to it."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.initialization import initialize
from model_checker.algorithms.explicit.NatATL.Recall.solver import (
    solve_natatl_recall,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.game_structures.cgs import cgs_validation
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.utils.error_handler import create_error_response

logger = logging.getLogger(__name__)


def _core_natatl_recall_checking(cgs: CGS, formula: str) -> dict[str, Any]:
    """Core logic for NatATL with Recall."""
    try:
        # Every recall strategy ends with (true*, IDLE), so idle must be available
        # in every state; memoryless strategies end with a true rule instead.
        cgs_validation.validate_nat_idle_requirements(
            cgs.graph, cgs.get_number_of_agents()
        )
        model_path = cgs.filename
        k, ctl_formula, agents, _ = initialize(model_path, formula, cgs=cgs)
        return solve_natatl_recall(k, ctl_formula, agents, cgs, model_path)

    except ValueError as e:
        error_msg = str(e)
        if "atomic proposition" in error_msg.lower() or "atom" in error_msg.lower():
            return create_error_response("semantic", error_msg)
        raise
    except Exception as e:
        logger.exception("Unexpected error during NatATL Recall checking")
        return create_error_response(
            "system", f"Error during NatATL Recall checking: {str(e)}"
        )


model_checking = create_model_checking_entry("NatATL", _core_natatl_recall_checking)
