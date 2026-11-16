"""NatATL model checker with recall strategies: rules whose conditions are patterns
over the history, each profile checked with CTL on the model restricted to it."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.solver import (
    solve_natatl_recall,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_initialization import (  # noqa: E501
    initialize,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.utils.error_handler import create_error_response

logger = logging.getLogger(__name__)


def _core_natatl_recall_checking(cgs: CGS, formula: str) -> dict[str, Any]:
    """Core logic for NatATL with Recall."""
    try:
        k, ctl_formula, agents, filename, model_parser = initialize(
            cgs.filename, formula, cgs=cgs
        )
        return solve_natatl_recall(k, ctl_formula, agents, model_parser, filename)

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
