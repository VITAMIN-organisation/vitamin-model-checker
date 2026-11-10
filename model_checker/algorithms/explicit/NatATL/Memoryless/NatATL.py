"""NatATL model checker with memoryless strategies: tries the complexity bounds up to
k until a strategy wins."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Memoryless.solver import (
    solve_natatl_memoryless,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.strategies import (
    initialize,
)
from model_checker.utils.error_handler import (
    create_error_response,
    value_error_to_response,
)

logger = logging.getLogger(__name__)


def model_checking(formula: str, model_path: str) -> dict[str, Any]:
    """Main entry point for NatATL memoryless model checking."""
    if not formula or not formula.strip():
        return create_error_response("validation", "Formula not entered")

    if not model_path:
        return create_error_response("validation", "Model file not specified")

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
        return create_error_response("system", f"Model file not found: {model_path}")
    except ValueError as e:
        return value_error_to_response(str(e))
    except Exception as e:
        logger.exception("Unexpected error during NatATL verification")
        return create_error_response("system", f"Error during model checking: {str(e)}")
