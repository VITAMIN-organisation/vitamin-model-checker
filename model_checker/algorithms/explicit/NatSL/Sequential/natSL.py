"""NatSL time-oriented model-checking entry point."""

from model_checker.algorithms.explicit.NatSL.core import (
    model_checking as _model_checking,
)
from model_checker.utils.error_handler import create_error_response


def model_checking(formula, model):
    try:
        return _model_checking(formula, model, mode="time")
    except FileNotFoundError as exc:
        return create_error_response("system", str(exc))
    except (ValueError, TypeError) as exc:
        return create_error_response("validation", str(exc))
    except Exception as exc:
        return create_error_response("syntax", str(exc))
