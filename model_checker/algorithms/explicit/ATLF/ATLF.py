from model_checker.algorithms.explicit.ATLF.real_value_utils import set_value_tuple_list
from model_checker.algorithms.explicit.ATLF.solver import solve_tree
from model_checker.algorithms.explicit.shared import build_resolved_formula_tree
from model_checker.algorithms.explicit.shared.atom_utils import (
    boolean_constant,
    formula_leaves,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.error_handler import (
    create_error_response,
    unresolved_leaves_error,
)
from model_checker.utils.literals import parse_tuple_list_literal


def get_tuple_list_prop(cgs, prop):
    i = proposition_index(cgs.atomic_propositions, prop)
    if i is None:
        return None
    states = cgs.states
    values_for_states = []
    matrix = cgs.matrix_prop

    for index, source in enumerate(matrix):
        state_value = (states[index], source[i])
        values_for_states.append(state_value)
    return values_for_states


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
        return unresolved_leaves_error(
            formula_leaves(res_parsing), cgs.atomic_propositions
        )
    solve_tree(cgs, root)
    initial_state = cgs.initial_state
    value_initial_state = dict(parse_tuple_list_literal(root.value))[initial_state]
    return {
        "res": f"Result: {root.value}",
        "initial_state": f"Initial state {initial_state}: {value_initial_state}",
    }


def _resolve_atom(cgs, atom):
    """Map an atomic proposition to its per-state real values; `true` is 1 and `false` is 0 everywhere."""
    constant = boolean_constant(atom)
    if constant is not None:
        return str(set_value_tuple_list(cgs, 1.0 if constant else 0.0))
    couples = get_tuple_list_prop(cgs, atom)
    if couples is None:
        return None
    return str(couples)


model_checking = create_model_checking_entry("ATLF", _core_atlf_checking)
