"""TOL model checking."""

from functools import partial
from typing import Any

from model_checker.algorithms.explicit.shared.entry_result_wrappers import (
    run_explicit_entry_model_checking,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.TOL.solver import solve_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    collect_formula_clocks,
    extend_timed_cgs_clocks,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def _core_model_checking(formula: str, filename: str) -> dict[str, Any]:
    if not formula.strip():
        return {"res": "Error: formula not entered", "initial_state": ""}

    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse(formula.strip())
    if ast is None:
        err = parser.errors[0] if parser.errors else "Syntax Error"
        return {"res": err, "initial_state": ""}

    tcgs = TimedCGS()
    tcgs.read_file(filename)

    formula_clocks = collect_formula_clocks(ast, set(tcgs.clocks))
    extend_timed_cgs_clocks(tcgs, formula_clocks)

    zone_graph = ZoneGraph(tcgs)
    solve_tree(tcgs, zone_graph, ast)

    init_state = str(tcgs.initial_state)
    is_satisfied = verify_initial_state(init_state, ast.satisfying_states)
    return format_model_checking_result(ast.satisfying_states, init_state, is_satisfied)


model_checking = partial(run_explicit_entry_model_checking, _core_model_checking)
