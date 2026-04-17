"""
CTL Model Checker.

This module implements model checking for CTL formulas over transition systems
represented as Concurrent Game Structures (CGS). CTL is a branching-time logic
that reasons about all possible execution paths from a state.

Key Concepts:
- Path quantifiers: E (exists a path), A (all paths)
- Temporal operators: X (next), F (eventually), G (globally), U (until), R (release)
- Combinations: EX, AX, EF, AF, EG, AG, EU, AU, ER, AR

Algorithm:
- Tree-based model checking: parse formula into tree, evaluate bottom-up
- Pre-image computation: EX uses existential, AX uses universal pre-image
- Fixpoint computation: Least (EF, EU), Greatest (EG, AG via negation)

Why CTL over LTL:
- CTL can express "there exists a path" (LTL cannot)
- CTL has PTIME model checking complexity (vs PSPACE for LTL)
- CTL naturally handles branching behavior in concurrent systems
"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from model_checker.algorithms.explicit.CTL.solver import solve_tree
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    resolve_atom_with_constants,
    verify_initial_state,
)
from model_checker.engine.runner import (
    build_formula_tree,
    parse_state_set_literal,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _get_parser():
    return FormulaParserFactory.get_parser_instance("CTL")


# ---------------------------------------------------------
# MODEL CHECKING INTERFACE
# ---------------------------------------------------------


def _parse_and_build_ctl_tree(
    cgs: "CGS", formula: str
) -> Union[Dict[str, Any], Tuple[Any, None]]:
    """
    Parse a CTL formula and build the corresponding formula tree.

    Returns either a (root, None) tuple on success or (None, error_dict)
    when a syntax or semantic error is detected.
    """
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = _get_parser()
    res_parsing = parser.parse(formula)
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return None, create_syntax_error(error_msg)

    root = build_formula_tree(
        res_parsing,
        lambda atom: resolve_atom_with_constants(cgs, atom, parser),
    )
    if root is None:
        return None, create_semantic_error("The atom does not exist")

    return root, None


def _build_trace_from_operator_trace(
    cgs: "CGS",
    root_value: str,
    initial_state: str,
    operator_trace: Any,
    is_satisfied: bool,
) -> Any:
    """
    Build witness/counterexample trace from operator-level trace information.
    """
    from model_checker.algorithms.explicit.CTL.solver_with_trace import (
        extract_trace_for_result,
    )

    return extract_trace_for_result(
        cgs, root_value, initial_state, operator_trace, is_satisfied
    )


def _build_fallback_trace(
    cgs: "CGS",
    root_value: str,
    initial_state: str,
    is_satisfied: bool,
) -> Any:
    """
    Build a shortest-path witness or counterexample trace when no operator-level
    trace information is available.
    """
    from model_checker.algorithms.explicit.shared import (
        StateTrace,
        extract_shortest_trace,
        normalize_state_set,
    )

    result_states = normalize_state_set(parse_state_set_literal(root_value))
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
    """
    Format CTL model checking result, optionally including a trace.
    """
    if trace is not None:
        from model_checker.algorithms.explicit.shared import (
            create_verification_result,
            normalize_state_set,
        )

        result_states = normalize_state_set(parse_state_set_literal(root_value))

        verification_result = create_verification_result(
            states=result_states, initial_state=initial_state, trace=trace
        )
        return verification_result.to_dict()

    return format_model_checking_result(root_value, initial_state, is_satisfied)


def _core_ctl_checking(
    cgs: "CGS", formula: str, generate_trace: bool = False
) -> Dict[str, Any]:
    """
    Core CTL model checking logic.

    Args:
        cgs: Model parser instance (already loaded)
        formula: CTL formula string
        generate_trace: If True, generate witness/counterexample traces

    Returns:
        Dictionary with result or error information
    """
    root, error = _parse_and_build_ctl_tree(cgs, formula)
    if error is not None:
        return error

    operator_trace = None
    if generate_trace:
        from model_checker.algorithms.explicit.CTL.solver_with_trace import (
            solve_tree_with_trace,
        )

        operator_trace = solve_tree_with_trace(cgs, root, generate_trace=True)
    else:
        solve_tree(cgs, root)

    # Check if initial state satisfies the formula
    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, root.value)

    # Generate trace if requested
    trace = None
    if generate_trace and operator_trace is not None:
        trace = _build_trace_from_operator_trace(
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
    """
    Execute model checking for CTL formula.

    This is the main entry point for CTL model checking. It supports
    both file-based and pre-loaded model inputs, with optional witness/counterexample generation.

    Args:
        formula: CTL formula string
        filename: Path to model file
        preloaded_model: Optional pre-loaded CGS model for performance.
                        When provided, skips file I/O and re-parsing.
                        Used internally by NatATL pruning to avoid
                        re-reading the model on every CTL call.
        generate_trace: If True, generate witness/counterexample traces (default: False)

    Returns:
        Dictionary with keys:
        - "res": Result string (e.g., "Result: {s0, s1}")
        - "initial_state": Initial state verification string
        - "trace": (optional) Trace information if generate_trace=True
        - "error": (optional) Structured error information
    """
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
