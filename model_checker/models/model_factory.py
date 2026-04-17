"""Factory for creating game structure parser instances.

Detects game structure type (CGS, costCGS, capCGS) from files and
instantiates the correct parser.
"""

import logging
import os
from typing import Any, Union

from model_checker.discovery import discover_logic_resource

logger = logging.getLogger(__name__)

from model_checker.parsers.game_structures.cap_cgs.cap_cgs import capCGS
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import costCGS


def detect_model_type_from_file(filename: str) -> str:
    """Detect model type from model file content.

    Args:
        filename: Path to the model file.

    Returns:
        One of CGS, costCGS, or capCGS.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Model file not found: {filename}")

    with open(filename) as f:
        content = f.read()

    return detect_model_type_from_content(content)


def detect_model_type_from_content(content: str) -> str:
    """Detect model type from model file content string.

    Args:
        content: Model file content as string.

    Returns:
        One of CGS, costCGS, or capCGS.
    """
    if "Transition_With_Costs" in content or "Costs_for_actions" in content:
        return "costCGS"
    elif "Capacities" in content or "Capacities_assignment" in content:
        return "capCGS"
    return "CGS"


def create_model_parser(
    filename: str, expected_type: str = None
) -> Union[CGS, costCGS, capCGS]:
    """Create appropriate model parser instance based on model file content.

    Detects the game structure type and returns the appropriate parser.
    CGS-compatible formulas can use CGS, costCGS, or capCGS parsers.

    Args:
        filename: Path to the model file.
        expected_type: Optional expected model type. If provided, overrides detection.

    Returns:
        Instance of CGS, costCGS, or capCGS parser.

    Raises:
        FileNotFoundError: If model file doesn't exist.
        ValueError: If expected_type doesn't match detected type.
    """
    actual_type = expected_type or detect_model_type_from_file(filename)

    try:
        parser_class = discover_logic_resource(
            logic_name=actual_type,
            group="vitamin.models",
            fallback_module_template="model_checker.parsers.game_structures.{name}.{name}",
            fallback_attr=actual_type,
            resource_type_label="Model type"
        )
        return parser_class()
    except LookupError:
        if actual_type == "CGS":
            return CGS()
        if actual_type == "costCGS":
            return costCGS()
        if actual_type == "capCGS":
            return capCGS()

        raise ImportError(f"Unknown model type: '{actual_type}'.")
    except ImportError as e:
        raise e


def create_model_parser_for_logic(
    filename: str, logic_type: str = None
) -> Union[CGS, costCGS, capCGS]:
    """Create appropriate model parser instance based on formula type requirements.

    Args:
        filename: Path to the model file.
        logic_type: Logic type name (e.g., "ATL", "OATL", "CapATL").

    Returns:
        Instance of CGS, costCGS, or capCGS parser.
    """
    from model_checker.registries import get_expected_model_type

    expected_type = get_expected_model_type(logic_type)

    return create_model_parser(filename, expected_type)
