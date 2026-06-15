"""TOL temporal operators."""

import re
from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.TOL.preimage import triangle_down
from model_checker.parsers.formulas.TOL.tol_ply_parser import DemonicBinary, DemonicOp
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    extract_closest_constraint,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

_DEMONIC_COST_DIGITS = re.compile(r"\d+")


def handle_globally(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicOp) -> None:
    all_states = set(tcgs.states)
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.operand)
    operand_states = node.operand.satisfying_states
    node.satisfying_states = greatest_fixpoint(
        all_states,
        lambda states: operand_states
        & triangle_down(tcgs, zone_graph, bound, states, constraint),
    )


def handle_next(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicOp) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.operand)
    node.satisfying_states = triangle_down(
        tcgs, zone_graph, bound, node.operand.satisfying_states, constraint
    )


def handle_eventually(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicOp
) -> None:
    all_states = set(tcgs.states)
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.operand)
    operand_states = node.operand.satisfying_states
    node.satisfying_states = least_fixpoint(
        operand_states,
        lambda states: operand_states
        | (all_states & triangle_down(tcgs, zone_graph, bound, states, constraint)),
    )


def handle_until(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary
) -> None:
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.right)
    states1 = node.left.satisfying_states
    states2 = node.right.satisfying_states
    node.satisfying_states = least_fixpoint(
        states2,
        lambda states: states2
        | (states1 & triangle_down(tcgs, zone_graph, bound, states, constraint)),
    )


def handle_release(
    tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary
) -> None:
    all_states = set(tcgs.states)
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.right)
    states1 = node.left.satisfying_states
    states2 = node.right.satisfying_states
    node.satisfying_states = greatest_fixpoint(
        all_states,
        lambda states: states2
        & (states1 | triangle_down(tcgs, zone_graph, bound, states, constraint)),
    )


def handle_weak(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: DemonicBinary) -> None:
    all_states = set(tcgs.states)
    bound = int(_DEMONIC_COST_DIGITS.findall(node.demonic_cost)[0])
    constraint = extract_closest_constraint(node.left)
    states1 = node.left.satisfying_states
    states2 = node.right.satisfying_states
    states_weak = states1 | states2
    node.satisfying_states = greatest_fixpoint(
        all_states,
        lambda states: states_weak
        & (states2 | triangle_down(tcgs, zone_graph, bound, states, constraint)),
    )
