"""TOL model checking."""

from typing import Any

from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    region_graph_for_formula,
    timed_checking_result,
)
from model_checker.algorithms.explicit.TOL.solver import solve_tree
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import create_error_response


def _core_tol_checking(tcgs, formula: str) -> dict[str, Any]:
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse(formula.strip())
    if ast is None:
        err = parser.errors[0] if parser.errors else "Syntax Error"
        return create_error_response("syntax", err)

    zone_graph = region_graph_for_formula(tcgs, ast)
    solve_tree(tcgs, zone_graph, ast)
    return timed_checking_result(tcgs, zone_graph, ast.satisfying_regions)


model_checking = create_model_checking_entry("TOL", _core_tol_checking)
