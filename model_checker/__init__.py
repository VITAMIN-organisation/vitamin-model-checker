"""
VITAMIN Model Checker - Verification Tool for Multi-Agent Systems

This package provides model checking capabilities for various temporal logics
including CTL, ATL, LTL, and their extensions.
"""

from model_checker.api import (
    CGS,
    CapCGS,
    CostCGS,
    FormulaParserFactory,
    ModuleManifest,
    check_checker_conformance,
    check_parser_conformance,
    create_model_parser,
    create_model_parser_for_logic,
    create_syntax_error,
    create_system_error,
    create_validation_error,
    detect_model_type_from_content,
    detect_model_type_from_file,
    execute_model_checking_with_parser,
    format_model_checking_result,
)

__version__ = "1.0.0"

__all__ = [
    "execute_model_checking_with_parser",
    "FormulaParserFactory",
    "create_model_parser",
    "create_model_parser_for_logic",
    "detect_model_type_from_content",
    "detect_model_type_from_file",
    "create_validation_error",
    "create_syntax_error",
    "create_system_error",
    "format_model_checking_result",
    "CGS",
    "CostCGS",
    "CapCGS",
    "ModuleManifest",
    "check_parser_conformance",
    "check_checker_conformance",
    "__version__",
]
