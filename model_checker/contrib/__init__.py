"""Contrib utilities for external module integration."""

from .conformance import (
    check_checker_conformance,
    check_model_compatibility,
    check_parser_conformance,
)
from .manifest_schema import ModuleManifest

__all__ = [
    "ModuleManifest",
    "check_parser_conformance",
    "check_checker_conformance",
    "check_model_compatibility",
]
