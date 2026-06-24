"""TCTL model checking."""

from functools import partial
from typing import Any, Dict

from model_checker.algorithms.explicit.shared.entry_result_wrappers import (
    run_explicit_entry_model_checking,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
)
from model_checker.algorithms.explicit.TCTL.evaluators import (
    initial_location_satisfied,
)
from model_checker.algorithms.explicit.TCTL.solver import solve_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    collect_formula_clocks,
    extend_timed_cgs_clocks,
)
from model_checker.parsers.game_structures.timed_cgs.regions import (
    project_regions_to_locations,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def _core_model_checking(formula: str, filename: str) -> Dict[str, Any]:
    if not formula.strip():
        return {"res": "Error: no formula specified", "initial_state": ""}

    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse(formula.strip())
    if ast is None:
        err = parser.errors[0] if parser.errors else "Syntax error in formula"
        return {
            "res": err,
            "initial_state": "",
        }

    tcgs = TimedCGS()
    tcgs.read_file(filename)

    formula_clocks = collect_formula_clocks(ast, set(tcgs.clocks))
    extend_timed_cgs_clocks(tcgs, formula_clocks)

    zone_graph = ZoneGraph(tcgs)
    solve_tree(tcgs, zone_graph, ast)

    init_state = str(tcgs.initial_state)
    is_satisfied = initial_location_satisfied(
        zone_graph, init_state, ast.satisfying_regions
    )
    result_locations = project_regions_to_locations(ast.satisfying_regions)
    return format_model_checking_result(result_locations, init_state, is_satisfied)


model_checking = partial(run_explicit_entry_model_checking, _core_model_checking)
