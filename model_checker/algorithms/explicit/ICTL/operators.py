"""Operator handlers for ICTL model checking."""

from typing import TYPE_CHECKING, Set

from model_checker.algorithms.explicit.ICTL.preimage import (
    pre_image_all,
    pre_image_exist,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import greatest_fixpoint
from model_checker.utils.literals import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode


def handle_ax(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states_sat = parse_state_set_literal(node.left.value)
    node.value = str(pre_image_all(checker.edges, states_sat))


def handle_ex(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    node.value = str(
        pre_image_exist(checker.edges, parse_state_set_literal(node.left.value))
    )


def handle_eg(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states_sat = parse_state_set_literal(node.left.value)
    p = checker.states_set
    t = states_sat
    while p - t:
        p = t
        t = pre_image_exist(checker.edges, p) & states_sat
    node.value = str(p)


def handle_ag(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states_sat = parse_state_set_literal(node.left.value)
    edges = checker.edges

    def update(q1: Set[str]) -> Set[str]:
        return states_sat & pre_image_all(edges, q1)

    node.value = str(greatest_fixpoint(checker.states_set, update))


def handle_ef(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states_sat = parse_state_set_literal(node.left.value)
    p: Set[str] = set()
    t = states_sat
    while t - p:
        p.update(t)
        t = pre_image_exist(checker.edges, p)
    node.value = str(p)


def handle_af(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states_sat = parse_state_set_literal(node.left.value)
    all_states = checker.states_set
    p: Set[str] = set()
    t = states_sat
    while t - p:
        p.update(t)
        t = pre_image_all(checker.edges, p) & all_states
    node.value = str(p)


def handle_or(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 | states2)


def handle_and(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 & states2)


def handle_not(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    y = checker.states_set - parse_state_set_literal(node.left.value)
    node.value = str(checker.states_with_upset_in(y))


def handle_eu(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    p: Set[str] = set()
    t = states2
    while t - p:
        p.update(t)
        t = pre_image_exist(checker.edges, p) & states1
    node.value = str(p)


def handle_au(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    p: Set[str] = set()
    t = states2
    while t - p:
        p.update(t)
        t = pre_image_all(checker.edges, p) & states1
    node.value = str(p)


def handle_er(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    edges = checker.edges

    def update(q1: Set[str]) -> Set[str]:
        return states2 & (states1 | pre_image_exist(edges, q1))

    node.value = str(greatest_fixpoint(checker.states_set, update))


def handle_ar(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    edges = checker.edges

    def update(q1: Set[str]) -> Set[str]:
        return states2 & (states1 | pre_image_all(edges, q1))

    node.value = str(greatest_fixpoint(checker.states_set, update))


def handle_implies(checker: "ICTLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    y = checker.states_set.difference(states1).union(states2)
    node.value = str(checker.states_with_upset_in(y))
