from typing import Any, Dict

from model_checker.algorithms.explicit.ATLF.solver import solve_tree
from model_checker.engine.runner import (
    build_formula_tree,
    parse_tuple_list_literal,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _get_parser():
    return FormulaParserFactory.get_parser_instance("ATLF")


def get_tuple_list_prop(cgs, prop):
    i = cgs.get_atom_index(prop)
    if i is None:
        return None
    states = cgs.get_states()
    values_for_states = []
    matrix = cgs.get_matrix_proposition()

    for index, source in enumerate(matrix):
        state_value = (states[index], float(source[i]))
        values_for_states.append(state_value)
    return values_for_states


def build_tree(cgs, tpl):
    return build_formula_tree(
        tpl,
        lambda atom: _resolve_atom(cgs, atom),
    )


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def get_value_initial_state(initial_state, string):
    """Returns the value of the model checking in the initial state."""
    list_tuple = parse_tuple_list_literal(string)
    for element in list_tuple:
        if element[0] == initial_state:
            return element[1]
    return 0.0  # Default value if not found


def _core_atlf_checking(cgs, formula):
    """
    Core ATLF model checking logic.

    Args:
        cgs: Model parser instance
        formula: ATLF formula string

    Returns:
        Dictionary with result or error information
    """
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("The atom does not exist")
    solve_tree(cgs, root)
    initial_state = cgs.get_initial_state()
    value_initial_state = get_value_initial_state(initial_state, root.value)
    result = {
        "res": "Result: " + str(root.value),
        "initial_state": (
            "Initial state " + str(initial_state) + ": " + str(value_initial_state)
        ),
    }
    return result


def model_checking(formula: str, filename: str) -> Dict[str, Any]:
    """
    Execute model checking for ATLF formula.

    Args:
        formula: ATLF formula string
        filename: Path to model file

    Returns:
        Dictionary with keys:
        - "res": Result string
        - "initial_state": Initial state verification string
        - "error": (optional) Structured error information
    """
    from model_checker.engine.runner import (
        execute_model_checking_with_parser,
    )

    return execute_model_checking_with_parser(
        formula, filename, "ATLF", _core_atlf_checking
    )


def _resolve_atom(cgs, atom):
    """
    Resolve atomic proposition into the stringified tuple list of (state, value).
    """
    couples = get_tuple_list_prop(cgs, atom)
    if couples is None:
        return None
    return str(couples)
