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


def undeclared_propositions_message(names, declared) -> str:
    """The message for formula names the model does not declare, listing them and the declared ones."""
    listed = ", ".join(repr(name) for name in sorted(names))
    return (
        f"Proposition(s) {listed} not among the model's declared "
        f"propositions {sorted(map(str, declared))}"
    )


def _undeclared(names, declared) -> set[str]:
    return {str(name) for name in names} - {str(p) for p in declared}


def raise_if_undeclared(names, declared) -> None:
    """Raise a semantic ValueError naming every one of `names` that is not in `declared`."""
    undeclared = _undeclared(names, declared)
    if undeclared:
        raise ValueError(
            f"[SEMANTIC] {undeclared_propositions_message(undeclared, declared)}"
        )


_CONSTANTS = frozenset({"true", "false"})


def unresolved_leaves_error(leaves, declared) -> dict[str, Any]:
    """The semantic error result when a solver could not resolve every leaf of the formula.

    Names the undeclared propositions; failing that, the constants this logic does
    not evaluate; failing that, every leaf it could not resolve.
    """
    leaves = {str(leaf) for leaf in leaves}
    undeclared = _undeclared(leaves - _CONSTANTS, declared)
    if undeclared:
        message = undeclared_propositions_message(undeclared, declared)
    elif leaves & _CONSTANTS:
        listed = ", ".join(repr(c) for c in sorted(leaves & _CONSTANTS))
        message = f"This logic does not evaluate the constant(s) {listed}"
    else:
        listed = ", ".join(repr(leaf) for leaf in sorted(leaves))
        message = f"This logic could not resolve the name(s) {listed} in the model"
    return create_error_response("semantic", message)


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
