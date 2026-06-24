"""Operator handlers for IATL model checking."""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode

_CoalitionPreimage = Callable[[str, set[str]], set[str]]

_COALITION_FROM_NODE = re.compile(r"^([<\[])([\d,]+)([>\]])")


def coalition_from_node(node_value: str) -> str:
    match = _COALITION_FROM_NODE.match(node_value)
    if match is None:
        raise ValueError(f"Invalid coalition operator label: {node_value!r}")
    return match.group(2)


def _greatest_g_states(
    checker: "IATLModelChecker",
    coalition: str,
    phi_states: set[str],
    pre_image: _CoalitionPreimage,
) -> set[str]:
    def update(current: set[str]) -> set[str]:
        return pre_image(coalition, current) & phi_states

    return greatest_fixpoint(checker.states_set.copy(), update)


def _least_f_states(
    checker: "IATLModelChecker",
    coalition: str,
    phi_states: set[str],
    pre_image: _CoalitionPreimage,
) -> set[str]:
    def update(current: set[str]) -> set[str]:
        return current | pre_image(coalition, current)

    return least_fixpoint(phi_states, update)


def _least_until_states(
    checker: "IATLModelChecker",
    coalition: str,
    states1: set[str],
    states2: set[str],
    pre_image: _CoalitionPreimage,
) -> set[str]:
    def update(accumulated: set[str]) -> set[str]:
        return accumulated | (pre_image(coalition, accumulated) & states1)

    return least_fixpoint(states2, update)


def _greatest_release_states(
    checker: "IATLModelChecker",
    coalition: str,
    states1: set[str],
    states2: set[str],
    pre_image: _CoalitionPreimage,
) -> set[str]:
    def update(current: set[str]) -> set[str]:
        return states2 & (states1 | pre_image(coalition, current))

    return greatest_fixpoint(checker.states_set.copy(), update)


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
    node.value = str(checker.pre_forall(coalition, states))


def handle_coalition_globally_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)
    node.value = str(
        _greatest_g_states(checker, coalition, phi_states, checker.pre_exists)
    )


def handle_coalition_globally_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)
    node.value = str(
        _greatest_g_states(checker, coalition, phi_states, checker.pre_forall)
    )


def handle_coalition_eventually_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)
    node.value = str(
        _least_f_states(checker, coalition, phi_states, checker.pre_exists)
    )


def handle_coalition_eventually_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)
    node.value = str(
        _least_f_states(checker, coalition, phi_states, checker.pre_forall)
    )


def handle_coalition_until_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(
        _least_until_states(checker, coalition, states1, states2, checker.pre_exists)
    )


def handle_coalition_until_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(
        _least_until_states(checker, coalition, states1, states2, checker.pre_forall)
    )


def handle_coalition_release_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(
        _greatest_release_states(
            checker, coalition, states1, states2, checker.pre_exists
        )
    )


def handle_coalition_release_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(
        _greatest_release_states(
            checker, coalition, states1, states2, checker.pre_forall
        )
    )
