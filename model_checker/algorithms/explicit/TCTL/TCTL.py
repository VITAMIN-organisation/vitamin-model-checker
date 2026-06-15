"""TCTL model checking."""

from functools import partial
from typing import Any, Dict

from model_checker.algorithms.explicit.shared.result_utils import (
    format_model_checking_result,
    run_explicit_entry_model_checking,
    verify_initial_state,
)
from model_checker.algorithms.explicit.TCTL.solver import solve_tree
from model_checker.parsers.formulas.TCTL import do_parsingTCTL
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def _core_model_checking(formula: str, filename: str) -> Dict[str, Any]:
    if not formula.strip():
        return {"res": "Error: no formula specified", "initial_state": ""}

    tcgs = TimedCGS()
    tcgs.read_file(filename)

    ast = do_parsingTCTL(formula.strip())
    if ast is None:
        return {
            "res": "Syntax error in formula or the atom doesn't exist",
            "initial_state": "",
        }

    zone_graph = ZoneGraph(tcgs)
    solve_tree(tcgs, zone_graph, ast)

    init_state = str(tcgs.initial_state)
    is_satisfied = verify_initial_state(init_state, ast.satisfying_states)
    return format_model_checking_result(ast.satisfying_states, init_state, is_satisfied)


model_checking = partial(run_explicit_entry_model_checking, _core_model_checking)
