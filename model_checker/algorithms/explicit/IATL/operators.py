"""Operator handlers for IATL model checking."""

import re
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode

_COALITION_FROM_NODE = re.compile(r"^([<\[])([\d,]+)([>\]])")


def coalition_from_node(node_value: str) -> str:
    match = _COALITION_FROM_NODE.match(node_value)
    if match is None:
        raise ValueError(f"Invalid coalition operator label: {node_value!r}")
    return match.group(2)


def handle_not(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    y = checker.states_set - parse_state_set_literal(node.left.value)
    node.value = str(checker.states_with_upset_in(y))


def handle_implies(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    y = checker.states_set.difference(states1).union(states2)
    node.value = str(checker.states_with_upset_in(y))


def handle_or(_checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 | states2)


def handle_and(_checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 & states2)


def handle_coalition_next_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states = parse_state_set_literal(node.left.value)
    node.value = str(checker.pre_exists(coalition, states))


def handle_coalition_next_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states = parse_state_set_literal(node.left.value)
    pre_forall = checker.pre_forall(coalition, states)
    node.value = str(checker.states_with_upset_in(pre_forall))


def handle_coalition_globally_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    def update(current):
        return checker.pre_exists(coalition, current) & phi_states

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))


def handle_coalition_globally_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    def update(current):
        return checker.pre_forall(coalition, current) & phi_states

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))


def handle_coalition_eventually_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    def update(current):
        return current | checker.pre_exists(coalition, current)

    node.value = str(least_fixpoint(phi_states, update))


def handle_coalition_eventually_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    def update(current):
        return current | checker.pre_forall(coalition, current)

    node.value = str(least_fixpoint(phi_states, update))


def handle_coalition_until_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update(accumulated):
        return accumulated | (checker.pre_exists(coalition, accumulated) & states1)

    node.value = str(least_fixpoint(states2, update))


def handle_coalition_until_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update(accumulated):
        return accumulated | (checker.pre_forall(coalition, accumulated) & states1)

    node.value = str(least_fixpoint(states2, update))


def handle_coalition_release_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update(q1):
        return states2 & (states1 | checker.pre_exists(coalition, q1))

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))


def handle_coalition_release_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)

    def update(q1):
        return states2 & (states1 | checker.pre_forall(coalition, q1))

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))
