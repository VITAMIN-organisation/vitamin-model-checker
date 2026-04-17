"""
NatATL Recall model checker.

Main entry point for verifying NatATL with recall strategies.
Integrates tree generation, regex/boolean pruning, and CTL model checking.
"""

import logging
from typing import Any, Dict

from model_checker.algorithms.explicit.NatATL.Recall.solver import (
    solve_natatl_recall,
)
from model_checker.algorithms.explicit.NatATL.Recall.strategy_initialization import (  # noqa: E501
    initialize,
)
from model_checker.engine.runner import execute_model_checking_with_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.utils.error_handler import (
    create_system_error,
)

logger = logging.getLogger(__name__)


def _core_natatl_recall_checking(cgs: CGS, formula: str) -> Dict[str, Any]:
    """Core logic for NatATL with Recall."""
    try:
        # Initialize model and parse formula
        (
            k,
            agent_actions,
            actions_list,
            atomic_propositions,
            ctl_formula,
            agents,
            filename,
            model_parser,
        ) = initialize(cgs.filename, formula)

        # Solve using the solver module
        result = solve_natatl_recall(
            k,
            agent_actions,
            actions_list,
            atomic_propositions,
            ctl_formula,
            agents,
            model_parser,
            filename,
        )

        return result

    except ValueError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during NatATL Recall checking")
        return create_system_error(f"Error during NatATL Recall checking: {str(e)}")


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """Main entry point for NatATL Recall."""
    return execute_model_checking_with_parser(
        formula, filename, "NatATL", _core_natatl_recall_checking
    )
