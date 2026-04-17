"""
Formula tree solver for CTL model checking.

Provides solve_tree (bottom-up evaluation only) and solve_tree_with_trace
(optional witness/counterexample generation) as two entry points. The trace
entry point consolidates all operator dispatch; solve_tree delegates to it
with generate_trace=False.
"""

from typing import TYPE_CHECKING, Any, Optional

from model_checker.algorithms.explicit.CTL.operators import (
    handle_af,
    handle_ag,
    handle_and,
    handle_ar,
    handle_au,
    handle_ax,
    handle_ef,
    handle_eg,
    handle_er,
    handle_eu,
    handle_ex,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.algorithms.explicit.CTL.operators_with_trace import (
    TRACE_HANDLERS,
    OperatorWithTrace,
)
from model_checker.algorithms.explicit.shared import (
    StateTrace,
    extract_shortest_trace,
    normalize_state_set,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _get_parser():
    return FormulaParserFactory.get_parser_instance("CTL")


_UNARY = {
    "NOT": handle_not,
    "EX": handle_ex,
    "AX": handle_ax,
    "EF": handle_ef,
    "AF": handle_af,
    "EG": handle_eg,
    "AG": handle_ag,
    "AR": handle_ar,
}
_BINARY = {
    "OR": handle_or,
    "AND": handle_and,
    "IMPLIES": handle_implies,
    "EU": handle_eu,
    "AU": handle_au,
    "ER": handle_er,
}


def _ctl_unary_key(parser_instance: Any, val: Any) -> Optional[str]:
    if parser_instance.verify("NOT", val):
        return "NOT"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("NEXT", val):
        return "EX"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("NEXT", val):
        return "AX"
    if parser_instance.verify("EXIST", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "EF"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "EVENTUALLY", val
    ):
        return "AF"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("GLOBALLY", val):
        return "EG"
    if parser_instance.verify("FORALL", val) and parser_instance.verify(
        "GLOBALLY", val
    ):
        return "AG"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("RELEASE", val):
        return "AR"
    return None


def _ctl_binary_key(parser_instance: Any, val: Any) -> Optional[str]:
    if parser_instance.verify("OR", val):
        return "OR"
    if parser_instance.verify("AND", val):
        return "AND"
    if parser_instance.verify("IMPLIES", val):
        return "IMPLIES"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("UNTIL", val):
        return "EU"
    if parser_instance.verify("FORALL", val) and parser_instance.verify("UNTIL", val):
        return "AU"
    if parser_instance.verify("EXIST", val) and parser_instance.verify("RELEASE", val):
        return "ER"
    return None


def _dispatch(
    key: Optional[str],
    handlers: dict,
    cgs: "CGS",
    node: Any,
    generate_trace: bool,
    cached_edges: list,
) -> Optional[Any]:
    if key is None or key not in handlers:
        return None
    h = handlers[key]
    h_trace = TRACE_HANDLERS.get(key)
    if h_trace and generate_trace:
        return h_trace(cgs, node, cached_edges)
    h(cgs, node)
    return None


def solve_tree_with_trace(
    cgs: "CGS", node: Any, generate_trace: bool = True
) -> Optional[OperatorWithTrace]:
    """
    Recursively solve the formula tree with optional trace generation.

    Formula is parsed into a binary tree; leaf nodes contain atomic propositions
    (resolved to state sets). Internal nodes apply CTL operators. When
    generate_trace is True, temporal operators that support it return
    OperatorWithTrace for witness/counterexample construction.

    Args:
        cgs: The CGS model instance
        node: Current tree node to evaluate
        generate_trace: If True, generate witness/counterexample traces

    Returns:
        OperatorWithTrace for the root temporal operator when generate_trace
        is True, otherwise None
    """
    if node.left is not None:
        solve_tree_with_trace(cgs, node.left, generate_trace)
    if node.right is not None:
        solve_tree_with_trace(cgs, node.right, generate_trace)

    operator_trace = None
    val = node.value

    # Get cached edges for trace generation to assume consistency and performance
    cached_edges = cgs.get_edges()

    if node.right is None:
        key = _ctl_unary_key(_get_parser(), val)
        operator_trace = _dispatch(key, _UNARY, cgs, node, generate_trace, cached_edges)
    elif node.left is not None and node.right is not None:
        key = _ctl_binary_key(_get_parser(), val)
        operator_trace = _dispatch(
            key, _BINARY, cgs, node, generate_trace, cached_edges
        )

    return operator_trace


def solve_tree(cgs: "CGS", node: Any) -> None:
    """
    Recursively solve the formula tree using bottom-up evaluation.

    Delegates to solve_tree_with_trace with generate_trace=False. Each node's
    value becomes the set of states where that subformula holds.

    Args:
        cgs: The CGS model instance
        node: Current tree node to evaluate
    """
    solve_tree_with_trace(cgs, node, generate_trace=False)


def extract_trace_for_result(
    cgs: "CGS",
    result_states_str: str,
    initial_state: str,
    operator_trace: Optional[OperatorWithTrace],
    is_satisfied: bool,
) -> Optional[StateTrace]:
    """
    Extract a concrete trace from the verification result.

    Args:
        cgs: The CGS model instance
        result_states_str: String representation of result states
        initial_state: Name of the initial state
        operator_trace: OperatorWithTrace from the main operator, or None
        is_satisfied: Whether the formula holds at the initial state

    Returns:
        StateTrace (witness or counterexample) or None if none can be built
    """
    if operator_trace is None:
        return None

    result_states = normalize_state_set(parse_state_set_literal(result_states_str))

    if is_satisfied:
        trace_type = "witness"
        target_states = result_states
        description = f"Witness: {operator_trace.description}"
    else:
        trace_type = "counterexample"
        target_states = cgs.all_states_set - result_states
        description = "Counterexample: Formula violated"

    if operator_trace.predecessors:
        from model_checker.algorithms.explicit.shared.trace_utils import (
            reconstruct_trace_from_predecessors,
        )

        trace_path = reconstruct_trace_from_predecessors(
            initial_state, target_states, operator_trace.predecessors
        )
        if trace_path:
            return StateTrace(
                states=trace_path, trace_type=trace_type, description=description
            )

    if target_states:
        trace_path = extract_shortest_trace(
            initial_state,
            target_states,
            cgs.all_states_set,
            cgs.get_edges(),
        )
        if trace_path:
            return StateTrace(
                states=trace_path, trace_type=trace_type, description=description
            )

    return None
