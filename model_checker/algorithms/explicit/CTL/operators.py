"""
CTL operator handlers for formula tree evaluation.

This module contains handler functions for all CTL operators, both unary
(NOT, EX, AX, EF, AF, EG, AG, AR) and binary (OR, AND, IMPLIES, EU, AU, ER).
"""

from typing import TYPE_CHECKING, Any, Set

from model_checker.algorithms.explicit.CTL.fixpoint import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.CTL.preimage import (
    pre_image_all,
    pre_image_exist,
    pre_release_universal,
)
from model_checker.algorithms.explicit.shared import (
    normalize_state_set,
    state_set_to_str,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_and as _bool_and,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_implies as _bool_implies,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_not as _bool_not,
)
from model_checker.algorithms.explicit.shared.boolean_operators import (
    handle_or as _bool_or,
)
from model_checker.engine.runner import parse_state_set_literal

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_not(cgs: "CGS", node: Any) -> None:
    """Handle NOT operator: complement of child's state set."""
    _bool_not(cgs, node, normalize_result=False)


def handle_ex(cgs: "CGS", node: Any) -> None:
    """Handle EX operator: there exists a next state satisfying phi."""
    states = parse_state_set_literal(node.left.value)
    reverse_index = (
        cgs.get_reverse_index() if hasattr(cgs, "get_reverse_index") else None
    )
    edges = cgs.get_edges()
    result = normalize_state_set(
        pre_image_exist(edges, states, reverse_index=reverse_index)
    )
    node.value = state_set_to_str(result)


def handle_ax(cgs: "CGS", node: Any) -> None:
    """Handle AX operator: all next states satisfy phi."""
    states = parse_state_set_literal(node.left.value)
    result = normalize_state_set(pre_image_all(cgs.get_edges(), cgs.states, states))
    node.value = state_set_to_str(result)


def handle_ef(cgs: "CGS", node: Any) -> None:
    """Handle EF operator: there exists a path eventually reaching phi."""
    target = parse_state_set_literal(node.left.value)
    edges = cgs.get_edges()
    reverse_index = (
        cgs.get_reverse_index() if hasattr(cgs, "get_reverse_index") else None
    )

    def update(T: Set[str]) -> Set[str]:
        return T.union(pre_image_exist(edges, T, reverse_index=reverse_index))

    result = least_fixpoint(target, update)
    node.value = state_set_to_str(result)


def _compute_af(cgs: "CGS", node: Any, cached_edges=None) -> Set[str]:
    """Compute AF phi = all_states - EG not_phi. Returns the state set."""
    all_states = cgs.all_states_set
    not_phi = all_states - parse_state_set_literal(node.left.value)
    edges = cached_edges if cached_edges is not None else cgs.get_edges()
    reverse_index = (
        cgs.get_reverse_index() if hasattr(cgs, "get_reverse_index") else None
    )

    def update(T: Set[str]) -> Set[str]:
        return not_phi.intersection(
            pre_image_exist(edges, T, reverse_index=reverse_index)
        )

    eg_not_phi = greatest_fixpoint(all_states.copy(), update)
    return all_states - eg_not_phi


def handle_af(cgs: "CGS", node: Any) -> None:
    """Handle AF operator: all paths eventually reach phi."""
    node.value = state_set_to_str(_compute_af(cgs, node))


def _compute_eg(cgs: "CGS", node: Any, cached_edges=None) -> Set[str]:
    """Compute EG phi. Returns the state set."""
    all_states = cgs.all_states_set
    target = parse_state_set_literal(node.left.value)
    edges = cached_edges if cached_edges is not None else cgs.get_edges()
    reverse_index = (
        cgs.get_reverse_index() if hasattr(cgs, "get_reverse_index") else None
    )

    def update(T: Set[str]) -> Set[str]:
        return target.intersection(
            pre_image_exist(edges, T, reverse_index=reverse_index)
        )

    return greatest_fixpoint(all_states.copy(), update)


def handle_eg(cgs: "CGS", node: Any) -> None:
    """Handle EG operator: there exists a path where phi holds globally."""
    node.value = state_set_to_str(_compute_eg(cgs, node))


def handle_ag(cgs: "CGS", node: Any) -> None:
    """Handle AG operator: all paths satisfy phi globally."""
    all_states = cgs.all_states_set
    not_phi = all_states - parse_state_set_literal(node.left.value)
    edges = cgs.get_edges()

    def update(T: Set[str]) -> Set[str]:
        return T.union(pre_image_exist(edges, T))

    ef_not_phi = least_fixpoint(not_phi, update)
    node.value = state_set_to_str(all_states - ef_not_phi)


def handle_ar(cgs: "CGS", node: Any) -> None:
    """Handle AR operator: universal release A(phi R psi)."""
    phi_states = parse_state_set_literal(node.left.value)
    psi_states = parse_state_set_literal(node.right.value)
    result = normalize_state_set(pre_release_universal(cgs, phi_states, psi_states))
    node.value = state_set_to_str(result)


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_or(cgs: "CGS", node: Any) -> None:
    """Handle OR operator: disjunction of two formulas."""
    _bool_or(cgs, node, normalize_result=True)


def handle_and(cgs: "CGS", node: Any) -> None:
    """Handle AND operator: conjunction of two formulas."""
    _bool_and(cgs, node, normalize_result=True)


def handle_implies(cgs: "CGS", node: Any) -> None:
    """Handle IMPLIES operator: phi -> psi = not phi or psi."""
    _bool_implies(cgs, node, normalize_result=False)


def handle_eu(cgs: "CGS", node: Any) -> None:
    """Handle EU operator: exists path where phi holds until psi."""
    phi_states = parse_state_set_literal(node.left.value)
    psi_states = parse_state_set_literal(node.right.value)
    edges = cgs.get_edges()
    reverse_index = (
        cgs.get_reverse_index() if hasattr(cgs, "get_reverse_index") else None
    )

    def update(T: Set[str]) -> Set[str]:
        return T.union(
            phi_states.intersection(
                pre_image_exist(edges, T, reverse_index=reverse_index)
            )
        )

    result = least_fixpoint(psi_states, update)
    node.value = state_set_to_str(result)


def _compute_au(cgs: "CGS", node: Any, cached_edges=None) -> Set[str]:
    """Compute A(phi U psi) = mu Y. psi or (phi and AX Y). Returns the state set."""
    phi_states = normalize_state_set(parse_state_set_literal(node.left.value))
    psi_states = parse_state_set_literal(node.right.value)
    all_states = cgs.all_states_set
    edges = cached_edges if cached_edges is not None else cgs.get_edges()

    def update(T: Set[str]) -> Set[str]:
        return T.union(phi_states.intersection(pre_image_all(edges, all_states, T)))

    return least_fixpoint(psi_states, update)


def handle_au(cgs: "CGS", node: Any) -> None:
    """Handle AU operator: all paths satisfy phi until psi."""
    node.value = state_set_to_str(_compute_au(cgs, node))


def handle_er(cgs: "CGS", node: Any) -> None:
    """Handle ER operator: existential release E(phi R psi)."""
    all_states = cgs.all_states_set
    not_phi = all_states - parse_state_set_literal(node.left.value)
    not_psi = all_states - parse_state_set_literal(node.right.value)
    edges = cgs.get_edges()

    def update(T: Set[str]) -> Set[str]:
        return T.union(
            not_phi.intersection(not_psi).intersection(
                pre_image_all(edges, all_states, T)
            )
        )

    a_not_phi_until = least_fixpoint(not_psi, update)
    node.value = state_set_to_str(all_states - a_not_phi_until)
