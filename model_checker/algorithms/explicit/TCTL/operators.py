"""TCTL temporal operators."""

from typing import TYPE_CHECKING

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.TCTL.preimage import pre_image_exist
from model_checker.parsers.formulas.TCTL import QuantifiedPath
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    extract_closest_constraint,
    zone_graph_pre_image_states,
)

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
    from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph


def handle_ef(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    constraint = extract_closest_constraint(node.formula)
    target = node.formula.satisfying_states
    node.satisfying_states = least_fixpoint(
        target,
        lambda states: states
        | zone_graph_pre_image_states(tcgs, zone_graph, states, constraint),
    )


def handle_af(tcgs: "TimedCGS", node: QuantifiedPath) -> None:
    all_states = set(tcgs.states)
    constraint = extract_closest_constraint(node.formula)
    target = all_states - node.formula.satisfying_states
    unreachable = least_fixpoint(
        target,
        lambda states: states | pre_image_exist(tcgs, states, constraints=constraint),
    )
    node.satisfying_states = all_states - unreachable


def handle_eg(tcgs: "TimedCGS", node: QuantifiedPath) -> None:
    all_states = set(tcgs.states)
    constraint = extract_closest_constraint(node.formula)
    target = node.formula.satisfying_states
    node.satisfying_states = greatest_fixpoint(
        all_states,
        lambda states: target.intersection(
            pre_image_exist(tcgs, states, constraints=constraint)
        ),
    )


def handle_ag(tcgs: "TimedCGS", zone_graph: "ZoneGraph", node: QuantifiedPath) -> None:
    all_states = set(tcgs.states)
    constraint = extract_closest_constraint(node.formula)
    target = all_states - node.formula.satisfying_states
    unreachable = least_fixpoint(
        target,
        lambda states: states
        | zone_graph_pre_image_states(tcgs, zone_graph, states, constraint),
    )
    node.satisfying_states = all_states - unreachable


def handle_eu(tcgs: "TimedCGS", node: QuantifiedPath) -> None:
    constraint = extract_closest_constraint(node.formula)
    states_phi = node.formula.left.satisfying_states
    states_psi = node.formula.right.satisfying_states
    node.satisfying_states = least_fixpoint(
        states_psi,
        lambda states: states
        | states_phi.intersection(
            pre_image_exist(tcgs, states, constraints=constraint)
        ),
    )


def handle_au(tcgs: "TimedCGS", node: QuantifiedPath) -> None:
    all_states = set(tcgs.states)
    constraint = extract_closest_constraint(node.formula)
    states_phi = node.formula.left.satisfying_states
    states_psi = node.formula.right.satisfying_states
    not_phi = all_states - states_phi
    not_psi = all_states - states_psi
    unreachable = least_fixpoint(
        not_psi,
        lambda states: states
        | not_phi.intersection(
            not_psi.intersection(pre_image_exist(tcgs, states, constraints=constraint))
        ),
    )
    node.satisfying_states = all_states - unreachable
