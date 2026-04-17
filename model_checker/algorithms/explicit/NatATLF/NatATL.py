import logging
from typing import Any, Dict

from model_checker.algorithms.explicit.NatATL.Memoryless.strategies import (
    initialize,
)

logger = logging.getLogger(__name__)


def model_checking(formula: str, model: str) -> Dict[str, Any]:
    """
    Executes NatATLF model checking.

    Args:
        formula: NatATLF formula string.
        model: Path to model file.

    Returns:
        Dictionary with Satisfiability, Complexity Bound, and Winning Strategy,
        or error dictionary.
    """
    from model_checker.utils.error_handler import (
        create_model_error,
        create_syntax_error,
        create_system_error,
        create_validation_error,
    )

    if not formula or not formula.strip():
        return create_validation_error("Formula not entered")

    if not model:
        return create_validation_error("Model file not specified")

    try:
        k, agent_actions, actions_list, atomic_propositions, CTLformula, agents, cgs = (
            initialize(model, formula)
        )

        from model_checker.algorithms.explicit.NatATL.Memoryless.solver import (
            solve_natatl_memoryless,
        )

        result = solve_natatl_memoryless(
            k,
            agent_actions,
            actions_list,
            atomic_propositions,
            CTLformula,
            agents,
            cgs,
            model,
        )

        # NatATLF uses a specific result format for 'res'
        is_satisfied = result.get("Satisfiability", False)
        result["res"] = f"Result: {'{satisfied}' if is_satisfied else '{}'}"

        return result
    except FileNotFoundError:
        return create_system_error(f"Model file not found: {model}")
    except ValueError as e:
        error_msg = str(e)
        if (
            "index" in error_msg.lower()
            or "dimension" in error_msg.lower()
            or "unrecognized" in error_msg.lower()
        ):
            return create_model_error(error_msg)
        if "formula" in error_msg.lower() or "parsing" in error_msg.lower():
            return create_syntax_error(error_msg)
        return create_system_error(error_msg)
    except Exception as e:
        return create_system_error(f"Error during model checking: {str(e)}")
