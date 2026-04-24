"""Standard public API for the model-checker library.

Exposes stable facades for model checking execution, parsing factories,
game structure models, and conformance utilities. New integrations update
this surface via ``model_checker.api_integrated``.
"""

from model_checker.algorithms.explicit.shared.result_utils import (
    format_model_checking_result,
)
from model_checker.contrib.conformance import (
    check_checker_conformance,
    check_parser_conformance,
)
from model_checker.contrib.manifest_schema import ModuleManifest
from model_checker.engine.runner import execute_model_checking_with_parser
from model_checker.models.model_factory import (
    create_model_parser,
    create_model_parser_for_logic,
    detect_model_type_from_content,
    detect_model_type_from_file,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cap_cgs.cap_cgs import CapCGS
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS
from model_checker.utils.error_handler import (
    create_syntax_error,
    create_system_error,
    create_validation_error,
)

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
]

from model_checker.api_integrated import *  # noqa: F401,F403
