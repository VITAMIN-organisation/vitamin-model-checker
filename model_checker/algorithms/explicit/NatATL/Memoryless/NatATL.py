"""
NatATL Memoryless model checker.

Iteratively explores strategy complexities (bound k) to find a winning strategy
using a memoryless verification algorithm.
"""

import logging
from typing import Any, Dict

from model_checker.algorithms.explicit.NatATL.Memoryless.solver import (
    solve_natatl_memoryless,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.strategies import (
    initialize,
)
from model_checker.utils.error_handler import (
    create_model_error,
    create_syntax_error,
    create_system_error,
    create_validation_error,
)

logger = logging.getLogger(__name__)


def model_checking(formula: str, model_path: str) -> Dict[str, Any]:
    """
    Executes NatATL (Memoryless) model checking.

    Args:
        formula: NatATL formula string.
        model_path: Path to model file.

    Returns:
        Dictionary with Satisfiability, Complexity Bound, and Winning Strategy,
        or error dictionary.
    """
    if not formula or not formula.strip():
        return create_validation_error("Formula not entered")

    if not model_path:
        return create_validation_error("Model file not specified")

    try:
        k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs = (
            initialize(model_path, formula)
        )

        return solve_natatl_memoryless(
            k,
            agent_actions,
            actions_list,
            atomic_propositions,
            CTLformula,
            agents,
            cgs,
            model_path,
        )

    except FileNotFoundError:
        return create_system_error(f"Model file not found: {model_path}")
    except ValueError as e:
        error_msg = str(e)
        if (
            "index" in error_msg.lower()
            or "dimension" in error_msg.lower()
            or "unrecognized" in error_msg.lower()
        ):
            return create_model_error(error_msg)
        # ValueError might also indicate syntax issues in formula parsing
        if "formula" in error_msg.lower() or "parsing" in error_msg.lower():
            return create_syntax_error(error_msg)
        return create_system_error(error_msg)
    except Exception as e:
        logger.exception("Unexpected error during NatATL verification")
        return create_system_error(f"Error during model checking: {str(e)}")
