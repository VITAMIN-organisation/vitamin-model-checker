"""CTL model checking on concurrent game structures."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from model_checker.algorithms.explicit.CTL.solver import (
    extract_trace_for_result,
    solve_tree_with_trace,
)
from model_checker.algorithms.explicit.shared import (
    build_resolved_formula_tree,
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _parse_and_build_ctl_tree(
    cgs: "CGS", formula: str
) -> Union[Dict[str, Any], Tuple[Any, None]]:
    """Parse the formula and build the tree, or return an error."""
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = FormulaParserFactory.get_parser_instance("CTL")
    res_parsing = parser.parse(formula)
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return None, create_syntax_error(error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return None, create_semantic_error("The atom does not exist")

    return root, None


def _build_fallback_trace(
    cgs: "CGS",
    root_value: str,
    initial_state: str,
    is_satisfied: bool,
) -> Any:
    """Build a shortest-path witness or counterexample when operator traces are missing."""
    from model_checker.algorithms.explicit.shared import (
        StateTrace,
        extract_shortest_trace,
    )

    result_states = {str(s) for s in parse_state_set_literal(root_value)}
    if is_satisfied:
        target_states = result_states
        trace_type = "witness"
        description = "Witness: path to satisfying state"
    else:
        target_states = cgs.all_states_set - result_states
        trace_type = "counterexample"
        description = "Counterexample: path to non-satisfying state"
    trace_path = extract_shortest_trace(
        initial_state,
        target_states,
        cgs.all_states_set,
        cgs.get_edges(),
    )
    if not trace_path:
        return None

    return StateTrace(states=trace_path, trace_type=trace_type, description=description)


def _format_ctl_result(
    root_value: str,
    initial_state: str,
    is_satisfied: bool,
    trace: Optional[Any],
) -> Dict[str, Any]:
    """Format the model checking result, with a trace when available."""
    if trace is not None:
        from model_checker.algorithms.explicit.shared import (
            create_verification_result,
        )

        result_states = {str(s) for s in parse_state_set_literal(root_value)}

        verification_result = create_verification_result(
            states=result_states, initial_state=initial_state, trace=trace
        )
        return verification_result.to_dict()

    return format_model_checking_result(root_value, initial_state, is_satisfied)


def _core_ctl_checking(
    cgs: "CGS", formula: str, generate_trace: bool = False
) -> Dict[str, Any]:
    """Run CTL model checking on a loaded model."""
    root, error = _parse_and_build_ctl_tree(cgs, formula)
    if error is not None:
        return error

    operator_trace = solve_tree_with_trace(cgs, root, generate_trace=generate_trace)

    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    trace = None
    if generate_trace and operator_trace is not None:
        trace = extract_trace_for_result(
            cgs, root.value, initial_state, operator_trace, is_satisfied
        )

    if generate_trace and trace is None:
        trace = _build_fallback_trace(cgs, root.value, initial_state, is_satisfied)

    return _format_ctl_result(root.value, initial_state, is_satisfied, trace)


def model_checking(
    formula: str,
    filename: str,
    preloaded_model: Optional["CGS"] = None,
    generate_trace: bool = False,
) -> Dict[str, Any]:
    """Entry point for CTL model checking from a file or a pre-loaded model."""
    if preloaded_model is not None:
        from model_checker.utils.error_handler import create_system_error

        if not formula or not formula.strip():
            from model_checker.utils.error_handler import (
                create_validation_error,
            )

            return create_validation_error("Formula not entered")

        try:
            if (
                not hasattr(preloaded_model, "states")
                or len(preloaded_model.states) == 0
            ):
                preloaded_model.read_file(filename)
            return _core_ctl_checking(preloaded_model, formula, generate_trace)
        except ValueError:
            raise
        except Exception as e:
            return create_system_error(f"Error during CTL model checking: {str(e)}")
    from model_checker.engine.runner import (
        execute_model_checking_with_parser,
    )

    def core_checking_wrapper(cgs, formula_str):
        return _core_ctl_checking(cgs, formula_str, generate_trace)

    return execute_model_checking_with_parser(
        formula, filename, "CTL", core_checking_wrapper
    )
