"""Shared helpers for COTL integration tests.

Used by test_correctness and test_semantics. Model-agnostic where possible:
derive state sets and atom lists from the loaded model instead of hardcoding.
"""

from model_checker.algorithms.explicit.COTL.COTL import model_checking
from model_checker.engine.runner import parse_state_set_literal
from model_checker.tests.helpers.model_helpers import load_test_model


def load_cotl_parser_from_file(path):
    """Load costCGS parser by reading the file at path (works for any path, e.g. temp)."""
    from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS

    parser = CostCGS()
    parser.read_file(str(path))
    return parser


def initial_state_name_from_path(path):
    """Return initial state name for the model at path (works for any path)."""
    parser = load_cotl_parser_from_file(path)
    return str(parser.get_initial_state()) if parser.get_initial_state() else None


def load_cotl_parser(model_path):
    test_data_dir = model_path.parents[2]
    return load_test_model(test_data_dir, "costCGS/COTL/cotl_model.txt")


def result_states(result):
    """Parse result set from result['res']."""
    res = result.get("res", "")
    if ": " not in res:
        return set()
    return parse_state_set_literal(res.split(": ", 1)[1])


def check_and_get_states(formula, model_path):
    """Run model_checking, assert no error, return (result, state set)."""
    result = model_checking(formula, str(model_path))
    assert "error" not in result, result.get("error", "")
    return result, result_states(result)


def states_where_prop_holds(model_path, prop):
    """Return set of state names where atomic proposition prop holds."""
    parser = load_cotl_parser(model_path)
    matrix = parser.get_matrix_proposition()
    idx = parser.get_atom_index(prop)
    if idx is None:
        return set()
    return {
        parser.get_state_name_by_index(i)
        for i, row in enumerate(matrix)
        if int(row[int(idx)]) == 1
    }


def atomic_propositions(model_path):
    """Return list of atomic proposition names in the model."""
    parser = load_cotl_parser(model_path)
    ap = parser.get_atomic_prop()
    if ap is None or len(ap) == 0:
        return []
    return [str(p) for p in ap]
