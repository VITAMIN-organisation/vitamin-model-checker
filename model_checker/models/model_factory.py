"""Factory for creating game structure parser instances.

Detects game structure type (CGS, costCGS, capCGS) from files and
instantiates the correct parser.
"""

import os
from typing import Union

from model_checker.discovery import discover_logic_resource
from model_checker.parsers.game_structures.cap_cgs.cap_cgs import CapCGS
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS


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
) -> Union[CGS, CostCGS, CapCGS]:
    """Create appropriate model parser instance based on model file content.

    Detects the game structure type or uses the expected type to resolve
    the parser class from registered entry points.
    """
    actual_type = expected_type or detect_model_type_from_file(filename)

    try:
        parser_class = discover_logic_resource(
            logic_name=actual_type,
            group="vitamin.models",
            resource_type_label="Model type",
        )
    except LookupError as e:
        raise ImportError(f"Unknown or unsupported model type: '{actual_type}'.") from e

    return parser_class()


def create_model_parser_for_logic(
    filename: str, logic_type: str = None
) -> Union[CGS, CostCGS, CapCGS]:
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
