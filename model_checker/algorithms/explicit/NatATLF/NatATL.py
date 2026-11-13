import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Memoryless.strategies import (
    initialize,
)

logger = logging.getLogger(__name__)


def model_checking(formula: str, model: str) -> dict[str, Any]:
    """NatATLF model checking of `formula` on the model file `model`: a dict with
    Satisfiability, Complexity Bound and Winning Strategy, or an error dict."""
    from model_checker.utils.error_handler import (
        create_error_response,
        value_error_to_response,
    )

    if not formula or not formula.strip():
        return create_error_response("validation", "Formula not entered")

    if not model:
        return create_error_response("validation", "Model file not specified")

    try:
        k, ctl_formula, agents, cgs = initialize(model, formula)

        from model_checker.algorithms.explicit.NatATL.Memoryless.solver import (
            solve_natatl_memoryless,
        )

        return solve_natatl_memoryless(k, ctl_formula, agents, cgs, model)
    except FileNotFoundError:
        return create_error_response("system", f"Model file not found: {model}")
    except ValueError as e:
        return value_error_to_response(str(e))
    except Exception as e:
        return create_error_response("system", f"Error during model checking: {str(e)}")
