"""CTL model checking on concurrent game structures."""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.CTL.solver import operator_key, solve_tree
from model_checker.algorithms.explicit.CTL.traces import RootOperands, build_trace
from model_checker.algorithms.explicit.shared import (
    StateTrace,
    build_resolved_formula_tree,
    create_verification_result,
)
from model_checker.algorithms.explicit.shared.atom_utils import formula_leaves
from model_checker.engine.execution import execute_model_checking_with_parser
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_error_response,
    unresolved_leaves_error,
    value_error_to_response,
)
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _parse_and_build_ctl_tree(
    cgs: "CGS", formula: str, parser: Any
) -> tuple[Any, dict[str, Any] | None]:
    """Parse the formula and build the tree, or return an error."""
    res_parsing = parser.parse(formula)
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return None, create_error_response("syntax", error_msg)

    root = build_resolved_formula_tree(cgs, res_parsing, parser)
    if root is None:
        return None, unresolved_leaves_error(
            formula_leaves(res_parsing), cgs.atomic_propositions
        )

    return root, None


def _root_trace(
    cgs: "CGS", root: Any, root_key: str | None, result: set[str]
) -> StateTrace | None:
    """The trace of the root operator, read from the solved tree."""

    def operand(node: Any) -> set[str]:
        return set() if node is None else parse_state_set_literal(node.value)

    operands = RootOperands(
        initial_state=cgs.initial_state,
        phi=operand(root.left),
        psi=operand(root.right),
        result=result,
        all_states=cgs.all_states_set,
        # Plain str, so the trace does not carry the model's numpy strings.
        edges=[(str(source), str(target)) for source, target in cgs.get_edges()],
    )
    return build_trace(root_key, operands)


def _core_ctl_checking(
    cgs: "CGS", formula: str, generate_trace: bool = False
) -> dict[str, Any]:
    """Run CTL model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("CTL")
    root, error = _parse_and_build_ctl_tree(cgs, formula, parser)
    if error is not None:
        return error

    # Read before solving: the solve replaces the operator with its state set.
    root_key = operator_key(parser, root)
    solve_tree(cgs, root, parser)

    states = parse_state_set_literal(root.value)
    trace = _root_trace(cgs, root, root_key, states) if generate_trace else None
    result = create_verification_result(
        states=states, initial_state=cgs.initial_state, trace=trace
    )
    return result.to_dict() if generate_trace else result.to_compact_dict()


def model_checking(
    formula: str,
    filename: str,
    preloaded_model: "CGS | None" = None,
    generate_trace: bool = False,
) -> dict[str, Any]:
    """Entry point for CTL model checking from a file or a pre-loaded model."""
    if preloaded_model is not None:
        if not formula or not formula.strip():
            return create_error_response("validation", "Formula not entered")

        try:
            if (
                not hasattr(preloaded_model, "states")
                or len(preloaded_model.states) == 0
            ):
                preloaded_model.read_file(filename)
            return _core_ctl_checking(preloaded_model, formula, generate_trace)
        except ValueError as exc:
            return value_error_to_response(str(exc))
        except Exception as e:
            return create_error_response(
                "system", f"Error during CTL model checking: {str(e)}"
            )

    def core_checking_wrapper(cgs, formula_str):
        return _core_ctl_checking(cgs, formula_str, generate_trace)

    return execute_model_checking_with_parser(
        formula, filename, "CTL", core_checking_wrapper
    )
