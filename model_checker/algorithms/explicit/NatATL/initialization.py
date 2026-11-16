"""Model and formula setup shared by NatATL memoryless, NatATLF and NatATL Recall."""

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
    """Load the model unless `cgs` is given, parse NatATL, and return k, the CTL
    goal, the coalition and the model."""
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Model file not found: {filename}")

    if cgs is None:
        cgs = CGS()
        cgs.read_file(filename)

    n = cgs.get_number_of_agents()
    CTLformula, agents, k = prepare_natatl_formula(formula, n)
    ensure_formula_atoms_exist(cgs, CTLformula)
    logger.debug("Involved agents: %s", agents)

    cgs_actions.validate_agent_numbers(agents, n)
    return k, CTLformula, agents, cgs
