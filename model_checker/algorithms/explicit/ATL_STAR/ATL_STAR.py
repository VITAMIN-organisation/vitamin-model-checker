"""ATL* model checking on concurrent game structures.

Automata-theoretic: the formula is reduced to a deterministic parity
automaton (`automata.Automaton.from_ltl`), producted with the CGS, and
solved as a 2-player parity game (see `verifier.py`). This is a different
approach from classical ATL's coalition pre-image fixpoint (`ATL/preimage.py`),
needed because ATL* allows unrestricted nesting of temporal operators
inside a coalition's path formula.
"""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.ATL_STAR import (
    cgs_adapter,
    strategy_export,
    verifier,
)
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import (
    create_model_checking_entry,
    execute_model_checking_with_parser,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.ATL_STAR.formula import Formula
from model_checker.utils.error_handler import create_error_response

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


class _ParseAdaptError(Exception):
    """Carries a pre-built VITAMIN error response, raised by `_parse_and_adapt`."""

    def __init__(self, response: dict[str, Any]) -> None:
        super().__init__(response.get("res", ""))
        self.response = response


def _parse_and_adapt(
    cgs: "CGS", formula: str
) -> tuple[Formula, cgs_adapter.AdaptedCGS]:
    """Parse `formula` and adapt `cgs`, the boilerplate every ATL_STAR entry
    point needs before it can do its own, different thing.

    Raises:
        _ParseAdaptError: parsing failed, or `cgs_adapter.adapt` rejected `cgs`.
    """
    parser = FormulaParserFactory.get_parser_instance("ATL_STAR")
    parsed_formula = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if parsed_formula is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        raise _ParseAdaptError(create_error_response("syntax", error_msg))

    try:
        model = cgs_adapter.adapt(cgs)
    except ValueError as e:
        raise _ParseAdaptError(create_error_response("semantic", str(e))) from e

    return parsed_formula, model


def _core_atl_star_checking(cgs: "CGS", formula: str) -> dict[str, Any]:
    """Run ATL* model checking on a loaded model."""
    try:
        parsed_formula, model = _parse_and_adapt(cgs, formula)
    except _ParseAdaptError as e:
        return e.response

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


def _core_synthesize_strategy(
    cgs: "CGS", formula: str, state: str | None
) -> dict[str, Any]:
    """Run ATL* strategy synthesis on a loaded model."""
    try:
        parsed_formula, model = _parse_and_adapt(cgs, formula)
    except _ParseAdaptError as e:
        return e.response

    try:
        parsed_formula = verifier.require_simple_coalition(parsed_formula)
    except ValueError as e:
        return create_error_response("semantic", str(e))

    try:
        resolved_state = verifier.resolve_state(model, state)
    except ValueError as e:
        return create_error_response("semantic", str(e))

    try:
        result = verifier.witness(parsed_formula, model, state=resolved_state)
    except ImportError as e:
        return create_error_response("environment", str(e))
    except ValueError as e:
        return create_error_response("semantic", str(e))

    if result is None:
        return {
            "res": f"Result: the formula does not hold at state {resolved_state}, no strategy to synthesize",
            "initial_state": f"State {resolved_state}: False",
            "satisfied": False,
            "strategy": None,
        }

    try:
        strategy = strategy_export.export_strategy(result)
    except ValueError as e:
        return create_error_response("semantic", str(e))

    return {
        "res": "Result: strategy synthesized",
        "initial_state": f"State {resolved_state}: True",
        "satisfied": True,
        "strategy": strategy,
    }


def synthesize_strategy(
    formula: str, filename: str, state: str | None = None
) -> dict[str, Any]:
    """Synthesize a JSON-serializable witness strategy for `formula` against
    the model in `filename`, at `state` (default: the model's own initial
    state).

    Only supports a formula whose outermost operator is a single coalition
    with no further coalition nested inside its path formula — broader
    formula shapes (nested coalitions such as `<<1>> G <<2>> F p`, or
    top-level combinations of coalitions such as `<<1>> F p & <<2>> G q`)
    are rejected with a clear error, deferred to a later iteration.
    Strategy synthesis is kept separate from `model_checking` so that entry
    point stays focused on plain ATL* model checking.
    """

    def _core(cgs: "CGS", formula_text: str) -> dict[str, Any]:
        return _core_synthesize_strategy(cgs, formula_text, state)

    return execute_model_checking_with_parser(
        formula, filename, logic_type="ATL_STAR", core_checking_func=_core
    )
