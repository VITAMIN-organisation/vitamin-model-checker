"""Factory for creating game structure parser instances.

Detects game structure type (CGS, costCGS, capCGS, WalletCGS, timedCGS,
BCGS, BirelationalMatrix) from files and instantiates the correct parser.
"""

import os
from typing import Callable

from model_checker.discovery import discover_logic_resource
from model_checker.parsers.game_structures.bcgs.bcgs import BCGS
from model_checker.parsers.game_structures.birelational_matrix.birelational_matrix import (
    BirelationalMatrix,
)
from model_checker.parsers.game_structures.cap_cgs.cap_cgs import CapCGS
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.wallet_cgs.wallet_cgs import WalletCGS

# Transition cells unique to ICTL birelational matrices (not CGS joint actions).
_BIRELATIONAL_CELL_TOKENS = frozenset({"0", "R", "P", "P,R"})
_BIRELATIONAL_MARKER_TOKENS = frozenset({"P", "P,R"})

_MODEL_SECTION_HEADERS = frozenset(
    {
        "Transition",
        "Unknown_Transition_by",
        "Name_State",
        "Initial_State",
        "Atomic_propositions",
        "Labelling",
        "Number_of_agents",
        "Agent_labels",
        "Wallets",
        "Clocks",
        "Clock_constraints",
        "Invariants",
        "Preorder",
        "Transition_With_Costs",
        "Costs_for_actions",
        "Costs_for_actions_split",
        "Capacities",
        "Capacities_assignment",
        "Actions_for_capacities",
    }
)


def _has_birelational_transition_cells(content: str) -> bool:
    """True when Transition rows use only 0/R/P/P,R and include a P marker."""
    in_transition = False
    found_marker = False
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in _MODEL_SECTION_HEADERS:
            if in_transition:
                break
            in_transition = line == "Transition"
            continue
        if not in_transition:
            continue
        tokens = line.split()
        if not tokens:
            continue
        if not all(token in _BIRELATIONAL_CELL_TOKENS for token in tokens):
            return False
        if any(token in _BIRELATIONAL_MARKER_TOKENS for token in tokens):
            found_marker = True
    return found_marker


def detect_model_type_from_file(filename: str) -> str:
    """Detect model type from model file content.

    Args:
        filename: Path to the model file.

    Returns:
        Detected model type id (e.g. CGS, costCGS, BirelationalMatrix).
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
        One of CGS, costCGS, capCGS, WalletCGS, timedCGS, BCGS, or
        BirelationalMatrix.
    """
    lines = {line.strip() for line in content.splitlines()}
    if "Wallets" in lines:
        return "WalletCGS"
    if "Clocks" in lines or "Clock_constraints" in lines:
        return "timedCGS"
    if (
        "Transition_With_Costs" in lines
        or "Costs_for_actions" in lines
        or "Costs_for_actions_split" in lines
    ):
        return "costCGS"
    if "Capacities" in lines or "Capacities_assignment" in lines:
        return "capCGS"
    if "Preorder" in lines:
        return "BCGS"
    if _has_birelational_transition_cells(content):
        return "BirelationalMatrix"
    return "CGS"


_MODEL_TYPE_CONSTRUCTORS: dict[
    str,
    Callable[
        [], CGS | CostCGS | CapCGS | BCGS | BirelationalMatrix | TimedCGS | WalletCGS
    ],
] = {
    "CGS": CGS,
    "costCGS": CostCGS,
    "capCGS": CapCGS,
    "WalletCGS": WalletCGS,
    "timedCGS": TimedCGS,
    "BCGS": BCGS,
    "BirelationalMatrix": BirelationalMatrix,
}


def _create_parser_direct(model_type: str):
    constructor = _MODEL_TYPE_CONSTRUCTORS.get(model_type)
    if constructor is None:
        raise ImportError(f"Unknown or unsupported model type: '{model_type}'.")
    return constructor()


def create_model_parser(
    filename: str, expected_type: str = None
) -> BCGS | CGS | CostCGS | CapCGS | BirelationalMatrix | TimedCGS | WalletCGS:
    """Create appropriate model parser instance based on model file content.

    Detects the game structure type or uses the expected type to resolve
    the parser class from registered entry points, with a direct-import
    fallback when entry points are unavailable.
    """
    actual_type = expected_type or detect_model_type_from_file(filename)

    try:
        parser_class = discover_logic_resource(
            logic_name=actual_type,
            group="vitamin.models",
            resource_type_label="Model type",
        )
    except LookupError:
        return _create_parser_direct(actual_type)

    return parser_class()


def create_model_parser_for_logic(
    filename: str, logic_type: str = None
) -> BCGS | CGS | CostCGS | CapCGS | BirelationalMatrix | TimedCGS | WalletCGS:
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
