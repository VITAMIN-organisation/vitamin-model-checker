"""TCTL model checking."""

from typing import Any

from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
)
from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    initial_region_satisfied,
)
from model_checker.algorithms.explicit.TCTL.solver import solve_tree
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    collect_formula_clocks,
    extend_timed_cgs_clocks,
    formula_clock_constants,
)
from model_checker.parsers.game_structures.timed_cgs.regions import (
    project_regions_to_locations,
)
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph
from model_checker.utils.error_handler import create_error_response


def _core_tctl_checking(tcgs, formula: str) -> dict[str, Any]:
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse(formula.strip())
    if ast is None:
        err = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", err)

    formula_clocks = collect_formula_clocks(ast, set(tcgs.clocks))
    extend_timed_cgs_clocks(tcgs, formula_clocks)

    zone_graph = ZoneGraph(tcgs, formula_clock_constants(ast, tcgs.clocks_dict))
    solve_tree(tcgs, zone_graph, ast)

    init_state = str(tcgs.initial_state)
    is_satisfied = initial_region_satisfied(zone_graph, ast.satisfying_regions)
    result_locations = project_regions_to_locations(ast.satisfying_regions)
    return format_model_checking_result(result_locations, init_state, is_satisfied)


model_checking = create_model_checking_entry("TCTL", _core_tctl_checking)
