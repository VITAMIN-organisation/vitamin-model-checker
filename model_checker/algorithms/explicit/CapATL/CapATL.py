"""CapATL model checker for capacity CGS models with knowledge-based reasoning."""

from model_checker.algorithms.explicit.CapATL.solver import (
    build_tree,
    solve_tree,
)
from model_checker.algorithms.explicit.CapATL.utils import (
    Omega_Y,
    X_agt_cap,
    build_state_cache,
    function_F_for_succ,
    indistinguishable_action,
    succ,
)
from model_checker.algorithms.explicit.shared.atom_utils import formula_leaves
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.CapATL.parser import KCAP_OPERATOR_PATTERN
from model_checker.utils.error_handler import (
    create_error_response,
    unresolved_leaves_error,
)


def _knowledge_operator(node) -> str | None:
    """The first knowledge operator (`K1`) in the parse tree, or None."""
    if isinstance(node, str):
        return node if KCAP_OPERATOR_PATTERN.match(node) else None
    if isinstance(node, tuple):
        for child in node:
            found = _knowledge_operator(child)
            if found:
                return found
    return None


def _validate_capatl_model(cgs):
    """Validate CapATL model structure."""
    if hasattr(cgs, "validity_model") and cgs.validity_model() is False:
        return create_error_response("model", "Incorrect model structure")
    return None


def _core_capatl_checking(cgs, formula):
    """Run CapATL model checking on a loaded model."""
    X_agt_cap.cache_clear()
    indistinguishable_action.cache_clear()
    function_F_for_succ.cache_clear()
    succ.cache_clear()
    Omega_Y.cache_clear()

    parser = FormulaParserFactory.get_parser_instance("CapATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    # The solver has no K semantics yet; without this check build_tree reports the
    # agent of `a is c` as a missing atom, or solve_tree skips K and fails later.
    knowledge_op = _knowledge_operator(res_parsing)
    if knowledge_op:
        return create_error_response(
            "validation",
            f"The knowledge operator {knowledge_op}(...) is parsed but not "
            "evaluated by the CapATL solver yet",
        )

    build_state_cache(cgs)

    root = build_tree(cgs, res_parsing)
    if root is None:
        return unresolved_leaves_error(
            formula_leaves(res_parsing), cgs.atomic_propositions
        )

    solve_tree(cgs, root)

    winning_states = set()
    for pk in root.value:
        winning_states.add(str(pk.state))

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, winning_states)
    return format_model_checking_result(winning_states, initial_state, is_satisfied)


model_checking = create_model_checking_entry(
    "CapATL",
    _core_capatl_checking,
    pre_validation_func=_validate_capatl_model,
)
