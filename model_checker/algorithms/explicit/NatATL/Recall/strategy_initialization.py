"""Model loading, validation, and formula parsing for NatATL Recall verification."""

import logging
import os
from typing import Any

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import prepare_natatl_formula
from model_checker.algorithms.explicit.shared.atom_utils import (
    ensure_formula_atoms_exist,
)
from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.game_structures.cgs import (
    CGSProtocol,
    cgs_actions,
    cgs_validation,
)

logger = logging.getLogger(__name__)


def initialize(
    model_path: str, formula: str, cgs: CGSProtocol | None = None
) -> tuple[int, str, list[int], str, Any]:
    """Load and validate the model, parse the NatATL formula, and return what the
    solver needs: `(k, CTLformula, agents, filename, model_parser)`. Pass `cgs` to
    reuse a loaded model."""
    filename = os.path.abspath(model_path)
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"No such file or directory: {filename}")

    if cgs is not None:
        model_parser = cgs
        states = getattr(model_parser, "states", None)
        if states is None or len(states) == 0:
            model_parser.read_file(filename)
    else:
        model_parser = create_model_parser_for_logic(filename, "NatATL")
        model_parser.read_file(filename)

    n = model_parser.get_number_of_agents()
    cgs_validation.validate_nat_idle_requirements(model_parser.graph, n)

    CTLformula, agents, k = prepare_natatl_formula(formula, n)
    ensure_formula_atoms_exist(model_parser, CTLformula)
    logger.debug("NatATL formula: %s", formula)
    logger.debug("Converted CTL formula: %s", CTLformula)
    logger.debug("States: %s", model_parser.states)
    logger.debug("Proposition matrix: %s", model_parser.matrix_prop)
    logger.debug("Involved agents: %s", agents)

    cgs_actions.validate_agent_numbers(agents, n)
    return k, CTLformula, agents, filename, model_parser
