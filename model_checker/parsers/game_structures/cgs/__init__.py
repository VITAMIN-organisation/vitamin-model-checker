"""CGS (Concurrent Game Structure) model parser.

Import the CGS class and protocols here to load and type CGS model usage.
"""

from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs.protocols import (
    CapCGSProtocol,
    CGSProtocol,
    CostCGSProtocol,
)

__all__ = ["CGS", "CGSProtocol", "CapCGSProtocol", "CostCGSProtocol"]
