from model_checker.algorithms.explicit.ATLF.solver import solve_tree
from model_checker.algorithms.explicit.shared import build_resolved_formula_tree
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.error_handler import create_error_response
from model_checker.utils.literals import parse_tuple_list_literal


def get_tuple_list_prop(cgs, prop):
    i = proposition_index(cgs.atomic_propositions, prop)
    if i is None:
        return None
    states = cgs.states
    values_for_states = []
    matrix = cgs.matrix_prop

    for index, source in enumerate(matrix):
        state_value = (states[index], float(source[i]))
        values_for_states.append(state_value)
    return values_for_states


def get_value_initial_state(initial_state, string):
    """Return the real-valued result at the initial state."""
    list_tuple = parse_tuple_list_literal(string)
    for element in list_tuple:
        if element[0] == initial_state:
            return element[1]
    return 0.0  # Default value if not found


def _core_atlf_checking(cgs, formula):
    """Run ATLF model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("ATLF")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    root = build_resolved_formula_tree(
        cgs, res_parsing, atom_resolver=lambda atom: _resolve_atom(cgs, atom)
    )
    if root is None:
        return create_error_response("semantic", "The atom does not exist")
    solve_tree(cgs, root)
    initial_state = cgs.initial_state
    value_initial_state = get_value_initial_state(initial_state, root.value)
    result = {
        "res": "Result: " + str(root.value),
        "initial_state": (
            "Initial state " + str(initial_state) + ": " + str(value_initial_state)
        ),
    }
    return result


def _resolve_atom(cgs, atom):
    """Map an atomic proposition to its per-state real values."""
    couples = get_tuple_list_prop(cgs, atom)
    if couples is None:
        return None
    return str(couples)


model_checking = create_model_checking_entry("ATLF", _core_atlf_checking)
