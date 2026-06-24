"""Formula tree solver for CTL model checking."""

from typing import TYPE_CHECKING, Any

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
    reconstruct_trace_from_predecessors,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


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


def _ctl_unary_key(parser_instance: Any, val: Any) -> str | None:
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


def _ctl_binary_key(parser_instance: Any, val: Any) -> str | None:
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
    key: str | None,
    handlers: dict,
    cgs: "CGS",
    node: Any,
    generate_trace: bool,
    cached_edges: list,
) -> Any | None:
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
) -> OperatorWithTrace | None:
    """Evaluate the formula tree bottom-up, optionally recording trace data."""
    if node.left is not None:
        solve_tree_with_trace(cgs, node.left, generate_trace)
    if node.right is not None:
        solve_tree_with_trace(cgs, node.right, generate_trace)

    operator_trace = None
    val = node.value

    cached_edges = cgs.get_edges()
    parser = FormulaParserFactory.get_parser_instance("CTL")

    if node.right is None:
        key = _ctl_unary_key(parser, val)
        operator_trace = _dispatch(key, _UNARY, cgs, node, generate_trace, cached_edges)
    elif node.left is not None and node.right is not None:
        key = _ctl_binary_key(parser, val)
        operator_trace = _dispatch(
            key, _BINARY, cgs, node, generate_trace, cached_edges
        )

    return operator_trace


def extract_trace_for_result(
    cgs: "CGS",
    result_states_str: str,
    initial_state: str,
    operator_trace: OperatorWithTrace | None,
    is_satisfied: bool,
) -> StateTrace | None:
    """Build a witness or counterexample trace from the verification result."""
    if operator_trace is None:
        return None

    result_states = {str(s) for s in parse_state_set_literal(result_states_str)}

    if is_satisfied:
        trace_type = "witness"
        target_states = result_states
        description = f"Witness: {operator_trace.description}"
    else:
        trace_type = "counterexample"
        target_states = cgs.all_states_set - result_states
        description = "Counterexample: Formula violated"

    if operator_trace.predecessors:
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
