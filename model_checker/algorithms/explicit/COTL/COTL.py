"""COTL model checking entry point; semantics in docs/COTL/algorithm.md."""

from model_checker.algorithms.explicit.COTL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.obstruction_model.obstruction_model import (
    ObstructionModel,
)
from model_checker.utils.error_handler import create_error_response


def _core_cotl_checking(model, formula):
    if not isinstance(model, ObstructionModel):
        return create_error_response(
            "validation",
            "COTL requires an obstruction model (a file with a Number_of_demons section)",
        )

    parser = FormulaParserFactory.get_parser_instance("COTL")
    parsed = parser.parse(formula, n_agent=model.number_of_demons)
    if parsed is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    root = build_resolved_formula_tree(model, parsed, parser)
    if root is None:
        return create_error_response(
            "semantic", "One or more atoms do not exist in the model"
        )

    solve_tree(model, root)

    initial_state = model.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)
    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry("COTL", _core_cotl_checking)
