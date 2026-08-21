"""
Handler functions for all CapATL operators
(
    unary: NOT/NEXT/EVENTUALLY/GLOBALLY;
    binary: AND/OR/UNTIL/RELEASE
).
"""

from model_checker.algorithms.explicit.CapATL.preimage import pre

from model_checker.algorithms.explicit.CapATL.utils import (
    pi_omega_Y,
    pi_theta,
    pointed_knowledge_set,
)


def handle_not(cgs, node):
    """Pointed-knowledge states that do not satisfy the negated operand."""
    all_pk = set(pointed_knowledge_set(cgs))
    node.value = all_pk - node.left.value


def handle_next(cgs, node, coal_str):
    """States from which the coalition can force the operand in one step."""
    target = list(node.left.value)
    omega_w = pi_omega_Y(cgs, target, coal_str)
    pre_w = pre(cgs, omega_w, coal_str)
    node.value = set(pi_theta(cgs, pre_w))


def handle_eventually(cgs, node, coal_str):
    """States from which the coalition can force phi in finitely many steps."""
    target = list(node.left.value)

    w_old = set()
    w_new = set(pi_omega_Y(cgs, target, coal_str))
    while not w_new.issubset(w_old):
        w_old |= w_new
        w_new = set(pre(cgs, list(w_old), coal_str))
    node.value = set(pi_theta(cgs, list(w_old)))


def handle_globally(cgs, node, coal_str):
    """States from which the coalition can keep phi true forever."""
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


def handle_and(cgs, node):
    """Pointed-knowledge states that satisfy both operands."""
    node.value = node.left.value & node.right.value


def handle_or(cgs, node):
    """Pointed-knowledge states that satisfy at least one operand."""
    node.value = node.left.value | node.right.value


def handle_implies(cgs, node):
    """Pointed-knowledge states that satisfy classical implication of the operands."""
    all_pk = set(pointed_knowledge_set(cgs))
    node.value = (all_pk - node.left.value) | node.right.value


def handle_until(cgs, node, coal_str):
    """States from which the coalition can force psi while keeping phi until then."""
    left_w = pi_omega_Y(cgs, list(node.left.value), coal_str)
    right_w = pi_omega_Y(cgs, list(node.right.value), coal_str)

    w_old = set()
    w_new = set(right_w)
    while not w_new.issubset(w_old):
        w_old |= w_new
        w_new = set(pre(cgs, list(w_old), coal_str)) & set(left_w)
    node.value = set(pi_theta(cgs, list(w_old)))


def handle_release(cgs, node, coal_str):
    """States from which the coalition can keep psi until (and including) phi releases it."""
    left_w = set(pi_omega_Y(cgs, list(node.left.value), coal_str))
    right_w = set(pi_omega_Y(cgs, list(node.right.value), coal_str))

    w_old = set(right_w)
    w_new = right_w & (left_w | set(pre(cgs, list(w_old), coal_str)))

    while not w_old.issubset(w_new):
        w_old = w_new
        w_new = right_w & (left_w | set(pre(cgs, list(w_old), coal_str)))
    node.value = set(pi_theta(cgs, list(w_old)))
