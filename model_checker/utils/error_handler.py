"""Standardized error response utilities for all logic implementations."""

import functools
from typing import Any


def create_error_response(
    error_type: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Error dict: ``res``, ``initial_state``, and nested ``error`` metadata."""
    return {
        "res": f"Error: {message}",
        "initial_state": "",
        "error": {
            "type": error_type,
            "message": message,
            "details": details or {},
        },
    }


_TAGGED_ERROR_PREFIXES = (
    ("[SEMANTIC]", functools.partial(create_error_response, "semantic")),
    ("[SYNTAX]", functools.partial(create_error_response, "syntax")),
    ("[MODEL]", functools.partial(create_error_response, "model")),
)

_SYNTAX_KEYWORDS = (
    "formula",
    "parsing",
    "syntax",
    "unexpected token",
    "syntactically",
    "invalid natatl",
    "could not extract",
)

_SEMANTIC_KEYWORDS = ("atom", "does not exist", "not found", "unknown")


def value_error_to_response(error_msg: str) -> dict[str, Any]:
    """Classify a ValueError message and return the matching error dict."""
    for tag, factory in _TAGGED_ERROR_PREFIXES:
        if tag in error_msg:
            return factory(error_msg.replace(tag, "").strip())

    lowered = error_msg.lower()
    if "index" in lowered or "dimension" in lowered:
        return create_error_response("model", error_msg)
    if any(keyword in lowered for keyword in _SYNTAX_KEYWORDS):
        return create_error_response("syntax", error_msg)
    if any(keyword in lowered for keyword in _SEMANTIC_KEYWORDS):
        return create_error_response("semantic", error_msg)

    return create_error_response("system", error_msg)
