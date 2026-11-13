"""Model and formula setup for NatATL memoryless verification."""

import logging
import os

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import prepare_natatl_formula
from model_checker.algorithms.explicit.shared.atom_utils import (
    ensure_formula_atoms_exist,
)
from model_checker.parsers.game_structures.cgs import CGS, cgs_actions

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str, cgs: CGS | None = None
) -> tuple[int, str, list[int], CGS]:
    """Load the model, parse NatATL, and return k, the CTL goal, the coalition and
    the model."""
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Model file not found: {filename}")

    if cgs is None:
        cgs = CGS()
        try:
            cgs.read_file(filename)
        except Exception as e:
            logger.error("Failed to read model file %s: %s", filename, e)
            raise

    try:
        CTLformula, agents, k = prepare_natatl_formula(
            formula, cgs.get_number_of_agents()
        )
    except ValueError as e:
        logger.error("Failed to parse or convert NatATL: %s", e)
        raise ValueError(f"Invalid NatATL formula format: {str(e)}") from e

    ensure_formula_atoms_exist(cgs, CTLformula)

    logger.debug("Involved agents: %s", agents)

    cgs_actions.validate_agent_numbers(agents, cgs.get_number_of_agents())
    return k, CTLformula, agents, cgs
