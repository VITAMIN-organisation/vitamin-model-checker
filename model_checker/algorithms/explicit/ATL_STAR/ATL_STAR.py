"""ATL* model checking on concurrent game structures.

Automata-theoretic: the formula is reduced to a deterministic parity
automaton (`automata.Automaton.from_ltl`), producted with the CGS, and
solved as a 2-player parity game (see `verifier.py`). This is a different
approach from classical ATL's coalition pre-image fixpoint (`ATL/preimage.py`),
needed because ATL* allows unrestricted nesting of temporal operators
inside a coalition's path formula.
"""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.ATL_STAR import cgs_adapter, verifier
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_error_response

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _core_atl_star_checking(cgs: "CGS", formula: str) -> dict[str, Any]:
    """Run ATL* model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("ATL_STAR")
    parsed_formula = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if parsed_formula is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    try:
        model = cgs_adapter.adapt(cgs)
    except ValueError as e:
        return create_error_response("semantic", str(e))

    try:
        satisfying_states = verifier.sat(parsed_formula, model)
    except ImportError as e:
        return create_error_response("environment", str(e))
    except ValueError as e:
        return create_error_response("semantic", str(e))

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, satisfying_states)

    return format_model_checking_result(satisfying_states, initial_state, is_satisfied)


model_checking = create_model_checking_entry("ATL_STAR", _core_atl_star_checking)
