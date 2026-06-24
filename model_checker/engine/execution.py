"""Model checking execution pipeline: validation, model loading, and dispatch."""

from collections.abc import Callable
from functools import partial
from typing import Any

from model_checker.models.model_factory import create_model_parser_for_logic
from model_checker.utils.error_handler import (
    create_error_response,
    value_error_to_response,
)


def validate_model_check_inputs(formula: str, filename: str) -> dict[str, Any] | None:
    """Return a validation error response, or None when inputs are acceptable."""
    if not formula or not formula.strip():
        return create_error_response("validation", "Formula not entered")
    if not filename:
        return create_error_response("validation", "Model file not specified")
    return None


def load_model_parser(filename: str, logic_type: str) -> Any:
    """Create a parser for the logic type and load the model file."""
    parser = create_model_parser_for_logic(filename, logic_type)
    parser.filename = filename
    parser.read_file(filename)
    return parser


def execute_model_checking_with_parser(
    formula: str,
    filename: str,
    logic_type: str,
    core_checking_func: Callable[[Any, str], dict[str, Any]],
    pre_validation_func: Callable[[Any], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    """Validate input, load the model, and run core_checking_func(parser, formula)."""
    validation_error = validate_model_check_inputs(formula, filename)
    if validation_error is not None:
        return validation_error

    try:
        parser = load_model_parser(filename, logic_type)

        if pre_validation_func is not None:
            pre_check_error = pre_validation_func(parser)
            if pre_check_error is not None:
                return pre_check_error

        return core_checking_func(parser, formula)

    except FileNotFoundError:
        return create_error_response("system", f"Model file not found: {filename}")
    except ValueError as exc:
        return value_error_to_response(str(exc))
    except Exception as exc:
        return create_error_response(
            "system", f"Error during model checking: {str(exc)}"
        )


PrefilterFunc = Callable[
    [str, str, Callable[[str, str], dict[str, Any]]],
    dict[str, Any],
]


def create_model_checking_entry(
    logic_type: str,
    core_checking_func: Callable[[Any, str], dict[str, Any]],
    pre_validation_func: Callable[[Any], dict[str, Any] | None] | None = None,
    *,
    prefilter_func: PrefilterFunc | None = None,
) -> Callable[[str, str], dict[str, Any]]:
    """Return a (formula, filename) entry point for a logic-specific checker."""
    full_checking = partial(
        execute_model_checking_with_parser,
        logic_type=logic_type,
        core_checking_func=core_checking_func,
        pre_validation_func=pre_validation_func,
    )
    if prefilter_func is None:
        return full_checking

    return partial(prefilter_func, full_checking=full_checking)
