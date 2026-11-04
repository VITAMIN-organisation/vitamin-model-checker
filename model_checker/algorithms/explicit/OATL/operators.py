"""OATL temporal operators as fixpoints of the demonic pre-image.

X is Proposition 1 of Catta et al. (AAMAS 2024); U and R are the least and
greatest fixpoints of Theorem 1. F, G and W are the derived forms
F phi = true U phi, G phi = false R phi and phi W psi = psi R (phi or psi).
"""

import math

from model_checker.algorithms.explicit.OATL.preimage import DemonicPreimage
from model_checker.algorithms.explicit.shared.cost_utils import (
    extract_coalition_and_cost,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.utils.literals import parse_state_set_literal


def _states(cgs, node_value: str) -> set[int]:
    return state_names_to_indices(cgs, parse_state_set_literal(node_value))


def _solve(cgs, node, pre: DemonicPreimage, fixpoint) -> None:
    """Store `fixpoint(step)` on the node, with `step` the bounded pre-image.

    The pre-image only grows as costs fall, so pricing missing costs at +inf and
    at 0 brackets every possible answer: if both agree, the gaps do not matter.
    """
    coalition, bound = extract_coalition_and_cost(node.value)

    def run(uncosted_cost: float) -> set[int]:
        return fixpoint(lambda target: pre(coalition, bound, target, uncosted_cost))

    result = run(math.inf)
    if pre.uncosted:
        undecided = run(0.0) - result
        if undecided:
            names = sorted(state_indices_to_names(cgs, undecided))
            raise ValueError(
                f"OATL: the truth of '{node.value}' at states {names} depends on "
                f"joint actions with no cost in the model: {pre.uncosted}"
            )
    node.value = str(tuple(sorted(state_indices_to_names(cgs, result))))


def handle_next(cgs, node, pre: DemonicPreimage) -> None:
    phi = _states(cgs, node.left.value)
    _solve(cgs, node, pre, lambda step: step(phi))


def handle_eventually(cgs, node, pre: DemonicPreimage) -> None:
    phi = _states(cgs, node.left.value)
    _solve(cgs, node, pre, lambda step: least_fixpoint(phi, lambda t: phi | step(t)))


def handle_globally(cgs, node, pre: DemonicPreimage) -> None:
    phi = _states(cgs, node.left.value)
    _solve(cgs, node, pre, lambda step: greatest_fixpoint(phi, lambda t: phi & step(t)))


def handle_until(cgs, node, pre: DemonicPreimage) -> None:
    phi = _states(cgs, node.left.value)
    psi = _states(cgs, node.right.value)
    _solve(
        cgs,
        node,
        pre,
        lambda step: least_fixpoint(psi, lambda t: psi | (phi & step(t))),
    )


def handle_release(cgs, node, pre: DemonicPreimage) -> None:
    phi = _states(cgs, node.left.value)
    psi = _states(cgs, node.right.value)
    _solve(
        cgs,
        node,
        pre,
        lambda step: greatest_fixpoint(psi, lambda t: psi & (phi | step(t))),
    )


def handle_weak_until(cgs, node, pre: DemonicPreimage) -> None:
    psi = _states(cgs, node.right.value)
    phi_or_psi = _states(cgs, node.left.value) | psi
    _solve(
        cgs,
        node,
        pre,
        lambda step: greatest_fixpoint(
            phi_or_psi, lambda t: phi_or_psi & (psi | step(t))
        ),
    )
