
"""Public entry point for compositional memoryless NatATL model checking."""

import logging
from typing import Any

from model_checker.algorithms.explicit.NatATL.Memoryless.modal_backend import (
    check_memoryless_formula,
)
from model_checker.utils.error_handler import (
    create_error_response,
    value_error_to_response,
)

logger = logging.getLogger(__name__)


def model_checking(formula: str, model_path: str, *, appropriateness="first-match", return_all_states=True) -> dict[str, Any]:
    """Check NatATL under bounded memoryless natural strategies."""

    if not isinstance(formula, str) or not formula.strip():
        return create_error_response(
            "validation", "Formula not entered"
        )

    if not model_path:
        return create_error_response(
            "validation", "Model file not specified"
        )

    try:
        return check_memoryless_formula(formula, model_path, appropriateness=appropriateness, return_all_states=return_all_states)

    except FileNotFoundError:
        return create_error_response(
            "system", f"Model file not found: {model_path}"
        )

    except ValueError as exc:
        message = str(exc)
        lower = message.lower()

        if lower.startswith("unknown atomic proposition:"):
            return create_error_response("semantic", message)

        if any(term in lower for term in (
            "wildcard",
            "transition relation",
            "original cgs must be total",
        )):
            return create_error_response("model", message)

        return value_error_to_response(message)

    except Exception as exc:
        logger.exception(
            "Unexpected failure in memoryless NatATL model checking"
        )

        return create_error_response(
            "system",
            f"Error during model checking: {exc}",
        )
