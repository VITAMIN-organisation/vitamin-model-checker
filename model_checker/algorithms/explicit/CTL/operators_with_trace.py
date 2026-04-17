"""
CTL operator handlers with witness/counterexample generation.

This module extends the standard CTL operators to generate traces that demonstrate
why formulas hold or don't hold. These traces are essential for debugging and
understanding verification results.
"""

from typing import Dict, List, Set, Tuple

from model_checker.algorithms.explicit.CTL.fixpoint import (
    least_fixpoint,
    least_fixpoint_with_trace,
)
from model_checker.algorithms.explicit.CTL.operators import (
    _compute_af,
    _compute_au,
    _compute_eg,
)
from model_checker.algorithms.explicit.CTL.preimage import (
    pre_image_all,
    pre_image_exist,
    pre_image_exist_with_trace,
)
from model_checker.algorithms.explicit.shared import (
    build_predecessor_map_forward,
    normalize_state_set,
    state_set_to_str,
)
from model_checker.algorithms.explicit.shared.verification_result import (
    TraceType,
)
from model_checker.engine.runner import parse_state_set_literal


class OperatorWithTrace:
    """
    Base class for CTL operators that generate traces.

    Stores the result states and optional predecessor map for trace reconstruction.
    """

    def __init__(self):
        self.result_states: Set[str] = set()
        self.predecessors: Dict[str, str] = {}
        self.trace_type: TraceType = TraceType.WITNESS
        self.description: str = ""


def handle_ex_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle EX operator with trace generation.

    For witness: shows a state and its successor that satisfies phi.
    """
    states = parse_state_set_literal(node.left.value)
    result_states, predecessors = pre_image_exist_with_trace(cached_edges, states)
    result_states = normalize_state_set(result_states)

    op = OperatorWithTrace()
    op.result_states = result_states
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "Transition to state satisfying phi"

    node.value = state_set_to_str(result_states)
    return op


def handle_ef_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle EF operator with trace generation.

    For witness: shows a path from initial state to a state satisfying phi.
    """
    target = parse_state_set_literal(node.left.value)

    def update_with_trace(T):
        new_states, new_preds = pre_image_exist_with_trace(cached_edges, T)
        return T.union(new_states), new_preds

    result, predecessors = least_fixpoint_with_trace(target, update_with_trace)

    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "Path eventually reaching phi"

    node.value = state_set_to_str(result)
    return op


def handle_ax_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle AX operator with trace generation.

    For counterexample: shows a state and a successor that doesn't satisfy phi.
    """
    states = parse_state_set_literal(node.left.value)
    result = normalize_state_set(
        pre_image_all(cached_edges, cgs.all_states_set, states)
    )

    # For counterexample, we need to find a state in result and a successor not in phi
    predecessors = {}

    # Build map of states to their bad successors (not in phi)
    all_states_set = cgs.all_states_set
    states_set = normalize_state_set(states)
    bad_successors = all_states_set - states_set

    for source, target in cached_edges:
        source_str = str(source)
        target_str = str(target)
        if source_str in result and target_str in bad_successors:
            if source_str not in predecessors:
                predecessors[source_str] = target_str

    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "All successors satisfy phi"

    node.value = state_set_to_str(result)
    return op


def handle_af_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle AF operator with trace generation.

    For witness: AF phi = !EG !phi. For counterexample: show path that stays in !phi forever.
    """
    result = _compute_af(cgs, node, cached_edges)
    node.value = state_set_to_str(result)
    predecessors = build_predecessor_map_forward(cached_edges, str(cgs.initial_state))
    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "All paths eventually reach phi"
    return op


def handle_eg_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle EG operator with trace generation.

    For witness: shows a cycle or infinite path where phi holds globally.
    """
    result = _compute_eg(cgs, node, cached_edges)
    node.value = state_set_to_str(result)
    eg_edges = [
        (s, t) for s, t in cached_edges if str(s) in result and str(t) in result
    ]
    predecessors = {}
    for source, target_state in eg_edges:
        source_str = str(source)
        target_str = str(target_state)
        if source_str not in predecessors:
            predecessors[source_str] = target_str
    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "Path where phi holds globally"
    return op


def handle_ag_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle AG operator with trace generation.

    For witness: AG phi holds when phi holds at every state on every path.
    A witness is a path that stays within the set of states satisfying AG phi.
    """
    all_states = cgs.all_states_set
    phi_states = parse_state_set_literal(node.left.value)
    not_phi = all_states - normalize_state_set(phi_states)

    def update(T: Set[str]) -> Set[str]:
        return T.union(pre_image_exist(cached_edges, T))

    ef_not_phi = least_fixpoint(not_phi, update)
    result = all_states - ef_not_phi
    node.value = state_set_to_str(result)

    ag_edges = [
        (s, t) for s, t in cached_edges if str(s) in result and str(t) in result
    ]
    predecessors = build_predecessor_map_forward(ag_edges, str(cgs.initial_state))
    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "Path where phi holds globally (AG)"
    return op


def handle_eu_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle EU operator with trace generation.

    For witness: shows path where phi holds until psi.
    """
    phi_states = parse_state_set_literal(node.left.value)
    psi_states = parse_state_set_literal(node.right.value)

    phi_set = normalize_state_set(phi_states)

    def update_with_trace(T):
        new_states, new_preds = pre_image_exist_with_trace(cached_edges, T)
        result_states = T.union(phi_set.intersection(new_states))
        # Filter predecessors to only those in phi
        filtered_preds = {s: p for s, p in new_preds.items() if s in phi_set}
        return result_states, filtered_preds

    result, predecessors = least_fixpoint_with_trace(psi_states, update_with_trace)

    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "Path where phi holds until psi"

    node.value = state_set_to_str(result)
    return op


def handle_au_with_trace(
    cgs, node, cached_edges: List[Tuple[str, str]]
) -> OperatorWithTrace:
    """
    Handle AU operator with trace generation.

    For witness: shows all paths reach psi with phi holding until then.
    """
    result = _compute_au(cgs, node, cached_edges)
    node.value = state_set_to_str(result)
    predecessors = build_predecessor_map_forward(cached_edges, str(cgs.initial_state))
    op = OperatorWithTrace()
    op.result_states = result
    op.predecessors = predecessors
    op.trace_type = TraceType.WITNESS
    op.description = "All paths reach psi with phi holding until then"
    return op


# Mapping from operator types to their trace-generating handlers
TRACE_HANDLERS = {
    "EX": handle_ex_with_trace,
    "AX": handle_ax_with_trace,
    "EF": handle_ef_with_trace,
    "AF": handle_af_with_trace,
    "EG": handle_eg_with_trace,
    "AG": handle_ag_with_trace,
    "EU": handle_eu_with_trace,
    "AU": handle_au_with_trace,
}
