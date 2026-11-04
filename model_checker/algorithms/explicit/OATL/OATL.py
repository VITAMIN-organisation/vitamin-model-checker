"""
OATL model checker over costCGS models (Catta et al., AAMAS 2024).

`<A><n> theta` holds when the Demon has a strategy that, at every step, erases
joint actions of total cost at most `n` so that, whatever coalition `A` does,
some remaining path satisfies `theta`. Agents outside `A` resolve the
remaining choices in the Demon's favour.
"""

from model_checker.algorithms.explicit.OATL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_error_response


def _core_oatl_checking(cgs, formula):
    if not hasattr(cgs, "get_cost_for_action"):
        return create_error_response(
            "validation", "OATL requires a costCGS model with action costs"
        )

    parser = FormulaParserFactory.get_parser_instance("OATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return create_error_response(
            "semantic", "One or more atoms do not exist in the model"
        )

    solve_tree(cgs, root)

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


# No ATL prefilter: <A><n> phi does not imply <A> phi, because the Demon and the
# agents outside A cooperate, so an ATL "False" would be wrong for OATL.
model_checking = create_model_checking_entry("OATL", _core_oatl_checking)
