"""Standardized error handling for model_checker backend.

This module provides utilities for creating consistent error responses
across all logic implementations.
"""

from typing import Any, Dict, Optional


def create_error_response(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create standardized error response dictionary.

    This provides a consistent error format that can be detected and processed
    by the API layer, while maintaining backward compatibility with string-based errors.

    Args:
        error_type: Error type category:
            - "syntax": Formula syntax errors
            - "semantic": Semantic errors (atom not found, etc.)
            - "model": Model structure/compatibility errors
            - "system": System errors (file not found, etc.)
            - "validation": Validation errors (missing agents, etc.)
        message: Human-readable error message
        details: Additional error context (optional)

    Returns:
        Dictionary with error information:
        {
            "res": "Error: {message}",  # Backward compatible string
            "initial_state": "",
            "error": {  # Structured error info (new)
                "type": error_type,
                "message": message,
                "details": details or {}
            }
        }
    """
    return {
        "res": f"Error: {message}",
        "initial_state": "",
        "error": {
            "type": error_type,
            "message": message,
            "details": details or {},
        },
    }


def create_syntax_error(
    message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a syntax error response."""
    return create_error_response("syntax", message, details)


def create_semantic_error(
    message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a semantic error response (e.g., atom not found)."""
    return create_error_response("semantic", message, details)


def create_model_error(
    message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a model structure/compatibility error response."""
    return create_error_response("model", message, details)


def create_system_error(
    message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a system error response (e.g., file not found)."""
    return create_error_response("system", message, details)


def create_validation_error(
    message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a validation error response (e.g., missing agents)."""
    return create_error_response("validation", message, details)
