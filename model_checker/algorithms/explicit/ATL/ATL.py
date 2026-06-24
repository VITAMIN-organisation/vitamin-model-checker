"""ATL model checking on concurrent game structures."""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
)
from model_checker.algorithms.explicit.ATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_error_response

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _core_atl_checking(cgs: "CGS", formula: str) -> dict[str, Any]:
    """Run ATL model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("ATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return create_error_response("semantic", "The atom does not exist")

    transition_cache = build_transition_cache(cgs)

    solve_tree(cgs, root, transition_cache)
    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry("ATL", _core_atl_checking)
