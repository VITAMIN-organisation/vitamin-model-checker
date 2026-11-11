"""Witness and counterexample traces for the root operator of a CTL formula.

A trace explains the root operator against the state sets of its operands: a
witness when an E-operator holds at the initial state, a counterexample when an
A-operator fails there. The other cases have no trace, because no single path
shows that an E-operator fails or that an A-operator holds.
"""

from collections.abc import Callable
from dataclasses import dataclass

from model_checker.algorithms.explicit.shared.trace_utils import (
    find_lasso,
    reconstruct_trace_bfs,
)
from model_checker.algorithms.explicit.shared.verification_result import (
    StateTrace,
    TraceType,
)

_Edges = list[tuple[str, str]]
_Trace = tuple[list[str], int | None]


@dataclass(frozen=True)
class RootOperands:
    """What a trace of the root operator is built from."""

    initial_state: str
    phi: set[str]
    psi: set[str]  # the right operand of an Until, empty for a unary operator
    result: set[str]
    all_states: set[str]
    edges: _Edges


def _step_into(targets: set[str], initial_state: str, edges: _Edges) -> _Trace | None:
    successor = next((t for s, t in edges if s == initial_state and t in targets), None)
    return None if successor is None else ([initial_state, successor], None)


def _path_to(targets: set[str], initial_state: str, edges: _Edges) -> _Trace | None:
    path = reconstruct_trace_bfs(edges, initial_state, targets)
    return None if path is None else (path, None)


def _ex_witness(op: RootOperands) -> _Trace | None:
    return _step_into(op.phi, op.initial_state, op.edges)


def _ax_counterexample(op: RootOperands) -> _Trace | None:
    return _step_into(op.all_states - op.phi, op.initial_state, op.edges)


def _ef_witness(op: RootOperands) -> _Trace | None:
    return _path_to(op.phi, op.initial_state, op.edges)


def _ag_counterexample(op: RootOperands) -> _Trace | None:
    return _path_to(op.all_states - op.phi, op.initial_state, op.edges)


def _eu_witness(op: RootOperands) -> _Trace | None:
    through_phi = [(s, t) for s, t in op.edges if s in op.phi]
    return _path_to(op.psi, op.initial_state, through_phi)


def _eg_witness(op: RootOperands) -> _Trace | None:
    return find_lasso(op.edges, op.initial_state, op.result)


def _lasso_outside_result(op: RootOperands) -> _Trace | None:
    # Outside AF phi every state has a successor outside it, and outside
    # A[phi U psi] every state where phi holds does, so a path can stay outside.
    return find_lasso(op.edges, op.initial_state, op.all_states - op.result)


def _au_broken_path(op: RootOperands) -> _Trace | None:
    before_psi = [(s, t) for s, t in op.edges if s not in op.psi]
    neither = op.all_states - op.phi - op.psi
    return _path_to(neither, op.initial_state, before_psi)


_Builder = Callable[[RootOperands], _Trace | None]

# (root operator, verdict at the initial state) -> the builders to try in order,
# each with what its trace shows.
_BUILDERS: dict[tuple[str | None, bool], list[tuple[_Builder, str]]] = {
    ("EX", True): [(_ex_witness, "a successor that satisfies phi")],
    ("EF", True): [(_ef_witness, "a path to a state that satisfies phi")],
    ("EU", True): [(_eu_witness, "a path through phi to a state that satisfies psi")],
    ("EG", True): [(_eg_witness, "a path on which phi holds forever")],
    ("AX", False): [(_ax_counterexample, "a successor that violates phi")],
    ("AG", False): [(_ag_counterexample, "a path to a state that violates phi")],
    ("AF", False): [(_lasso_outside_result, "a path on which phi never holds")],
    ("AU", False): [
        (_au_broken_path, "a path on which phi fails before psi holds"),
        (_lasso_outside_result, "a path on which psi never holds"),
    ],
}


def build_trace(key: str | None, op: RootOperands) -> StateTrace | None:
    """The trace for root operator ``key``, or None when the case has no trace."""
    holds = op.initial_state in op.result
    trace_type = TraceType.WITNESS if holds else TraceType.COUNTEREXAMPLE
    for build, shows in _BUILDERS.get((key, holds), []):
        trace = build(op)
        if trace is not None:
            states, cycle_start_index = trace
            return StateTrace(
                states=states,
                trace_type=trace_type,
                description=f"{trace_type.capitalize()}: {shows}",
                cycle_start_index=cycle_start_index,
            )
    return None
