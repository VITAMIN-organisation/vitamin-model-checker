"""
CapATL operator handlers for formula tree evaluation.

This module contains handler functions for all CapATL operators, both unary
(NOT, NEXT, EVENTUALLY, GLOBALLY) and binary (AND, OR, UNTIL).
"""

from model_checker.algorithms.explicit.CapATL.preimage import pre
from model_checker.algorithms.explicit.CapATL.utils import (
    pi_omega_Y,
    pi_theta,
    pointed_knowledge_set,
)

# ---------------------------------------------------------
# UNARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_not(cgs, node):
    """Handle NOT operator: complement of child's pointed knowledge set."""
    all_pk = set(pointed_knowledge_set(cgs))
    node.value = all_pk - node.left.value


def handle_next(cgs, node, coal_str):
    """Handle NEXT operator: coalition can force next transition to target."""
    target = list(node.left.value)
    omega_w = pi_omega_Y(cgs, target, coal_str)
    pre_w = pre(cgs, omega_w, coal_str)
    node.value = set(pi_theta(cgs, pre_w))


def handle_eventually(cgs, node, coal_str):
    """Handle EVENTUALLY operator: least fixpoint for coalition reachability."""
    target = list(node.left.value)

    w_old = set()
    w_new = set(pi_omega_Y(cgs, target, coal_str))
    while not w_new.issubset(w_old):
        w_old |= w_new
        w_new = set(pre(cgs, list(w_old), coal_str)) & set(
            pi_omega_Y(cgs, target, coal_str)
        )
    node.value = set(pi_theta(cgs, list(w_old)))


def handle_globally(cgs, node, coal_str):
    """Handle GLOBALLY operator: greatest fixpoint for coalition invariance."""
    target = list(node.left.value)

    w_old = set(pi_omega_Y(cgs, target, coal_str))
    w_new = set(pre(cgs, list(w_old), coal_str)) & set(
        pi_omega_Y(cgs, target, coal_str)
    )
    while not w_old.issubset(w_new):
        w_old = w_new
        w_new = set(pre(cgs, list(w_old), coal_str)) & set(
            pi_omega_Y(cgs, target, coal_str)
        )
    node.value = set(pi_theta(cgs, list(w_old)))


# ---------------------------------------------------------
# BINARY OPERATOR HANDLERS
# ---------------------------------------------------------


def handle_and(cgs, node):
    """Handle AND operator: intersection of two pointed knowledge sets."""
    node.value = node.left.value & node.right.value


def handle_or(cgs, node):
    """Handle OR operator: union of two pointed knowledge sets."""
    node.value = node.left.value | node.right.value


def handle_until(cgs, node, coal_str):
    """Handle UNTIL operator: least fixpoint for coalition until property."""
    left_w = pi_omega_Y(cgs, list(node.left.value), coal_str)
    right_w = pi_omega_Y(cgs, list(node.right.value), coal_str)

    w_old = set()
    w_new = set(right_w)
    while not w_new.issubset(w_old):
        w_old |= w_new
        w_new = set(pre(cgs, list(w_old), coal_str)) & set(left_w)
    node.value = set(pi_theta(cgs, list(w_old)))
