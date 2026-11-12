"""COTL temporal operators as fixpoints of the one-step operators in preimage.py.

X, F and U use `next_in`; WX, G, R and W use `next_in_or_stop`, so they also
hold on a path that stops because every edge out of its last state is disabled.
"""

from model_checker.algorithms.explicit.COTL.preimage import LegionSteps
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.parsers.formulas.COTL.parser import parse_legion_budget
from model_checker.utils.literals import parse_state_set_literal, state_set_literal


def _states(model, node_value: str) -> set[int]:
    return state_names_to_indices(model, parse_state_set_literal(node_value))


def _store(model, node, states: set[int]) -> None:
    node.value = state_set_literal(state_indices_to_names(model, states))


def _steps(node, steps: LegionSteps):
    legion, budget = parse_legion_budget(node.value)
    return (
        lambda target: steps.next_in(legion, budget, target),
        lambda target: steps.next_in_or_stop(legion, budget, target),
    )


def handle_next(model, node, steps: LegionSteps) -> None:
    next_in, _ = _steps(node, steps)
    _store(model, node, next_in(_states(model, node.left.value)))


def handle_weak_next(model, node, steps: LegionSteps) -> None:
    _, next_in_or_stop = _steps(node, steps)
    _store(model, node, next_in_or_stop(_states(model, node.left.value)))


def handle_eventually(model, node, steps: LegionSteps) -> None:
    next_in, _ = _steps(node, steps)
    phi = _states(model, node.left.value)
    _store(model, node, least_fixpoint(phi, lambda t: phi | next_in(t)))


def handle_globally(model, node, steps: LegionSteps) -> None:
    _, next_in_or_stop = _steps(node, steps)
    phi = _states(model, node.left.value)
    _store(model, node, greatest_fixpoint(phi, lambda t: phi & next_in_or_stop(t)))


def handle_until(model, node, steps: LegionSteps) -> None:
    next_in, _ = _steps(node, steps)
    phi = _states(model, node.left.value)
    psi = _states(model, node.right.value)
    _store(model, node, least_fixpoint(psi, lambda t: psi | (phi & next_in(t))))


def handle_release(model, node, steps: LegionSteps) -> None:
    _, next_in_or_stop = _steps(node, steps)
    phi = _states(model, node.left.value)
    psi = _states(model, node.right.value)
    _store(
        model,
        node,
        greatest_fixpoint(psi, lambda t: psi & (phi | next_in_or_stop(t))),
    )


def handle_weak_until(model, node, steps: LegionSteps) -> None:
    _, next_in_or_stop = _steps(node, steps)
    psi = _states(model, node.right.value)
    phi_or_psi = _states(model, node.left.value) | psi
    _store(
        model,
        node,
        greatest_fixpoint(
            phi_or_psi, lambda t: phi_or_psi & (psi | next_in_or_stop(t))
        ),
    )
