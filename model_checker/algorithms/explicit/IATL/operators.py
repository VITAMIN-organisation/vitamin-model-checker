"""Operator handlers for IATL model checking."""

import re
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.IATL.preimage import (
    pre_image_exists,
    pre_image_forall,
)
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
    closures = checker.upward_closure
    node.value = str(
        {state for state in checker.states_set if closures[str(state)].issubset(y)}
    )


def handle_implies(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    y = checker.states_set.difference(states1).union(states2)
    closures = checker.upward_closure
    node.value = str(
        {state for state in checker.states_set if closures[str(state)].issubset(y)}
    )


def handle_or(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 | states2)


def handle_and(checker: "IATLModelChecker", node: "FormulaTreeNode") -> None:
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(states1 & states2)


def handle_coalition_next_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states = parse_state_set_literal(node.left.value)
    node.value = str(
        pre_image_exists(
            checker.data["graph"],
            checker.data["states"],
            coalition,
            {str(state) for state in states},
            checker.data["number_of_agents"],
            transition_cache=checker.transition_cache_for(coalition),
        )
    )


def handle_coalition_next_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states = parse_state_set_literal(node.left.value)
    node.value = str(
        pre_image_forall(
            checker.data["graph"],
            checker.data["states"],
            coalition,
            {str(state) for state in states},
            checker.data["number_of_agents"],
            transition_cache=checker.transition_cache_for(coalition),
        )
    )


def handle_coalition_globally_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    cache = checker.transition_cache_for(coalition)

    def update(current):
        return (
            pre_image_exists(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in current},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            & phi_states
        )

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))


def handle_coalition_globally_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    cache = checker.transition_cache_for(coalition)

    def update(current):
        return (
            pre_image_forall(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in current},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            & phi_states
        )

    node.value = str(greatest_fixpoint(checker.states_set.copy(), update))


def handle_coalition_eventually_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    cache = checker.transition_cache_for(coalition)

    def update(current):
        return current | pre_image_exists(
            checker.data["graph"],
            checker.data["states"],
            coalition,
            {str(state) for state in current},
            checker.data["number_of_agents"],
            transition_cache=cache,
        )

    node.value = str(least_fixpoint(phi_states, update))


def handle_coalition_eventually_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    phi_states = parse_state_set_literal(node.left.value)

    cache = checker.transition_cache_for(coalition)

    def update(current):
        return current | pre_image_forall(
            checker.data["graph"],
            checker.data["states"],
            coalition,
            {str(state) for state in current},
            checker.data["number_of_agents"],
            transition_cache=cache,
        )

    node.value = str(least_fixpoint(phi_states, update))


def handle_coalition_until_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    cache = checker.transition_cache_for(coalition)
    accumulated = set()
    frontier = states2
    while frontier - accumulated:
        accumulated |= frontier
        frontier = (
            pre_image_exists(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in accumulated},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            & states1
        )
    node.value = str(accumulated)


def handle_coalition_until_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    cache = checker.transition_cache_for(coalition)
    accumulated = set()
    frontier = states2
    while frontier - accumulated:
        accumulated |= frontier
        frontier = (
            pre_image_forall(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in accumulated},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            & states1
        )
    node.value = str(accumulated)


def handle_coalition_release_exists(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    cache = checker.transition_cache_for(coalition)
    q1 = checker.states_set.copy()
    q3 = states2
    while not q1.issubset(q3):
        q1 &= q3
        q3 = (
            pre_image_exists(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in q1},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            | states1
        )
    node.value = str(q1)


def handle_coalition_release_forall(
    checker: "IATLModelChecker", node: "FormulaTreeNode"
) -> None:
    coalition = coalition_from_node(node.value)
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    cache = checker.transition_cache_for(coalition)
    q1 = checker.states_set.copy()
    q3 = states2
    while not q1.issubset(q3):
        q1 &= q3
        q3 = (
            pre_image_forall(
                checker.data["graph"],
                checker.data["states"],
                coalition,
                {str(state) for state in q1},
                checker.data["number_of_agents"],
                transition_cache=cache,
            )
            | states1
        )
    node.value = str(q1)
