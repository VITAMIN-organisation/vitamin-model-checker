"""
Formula tree solver for CapATL model checking.

This module contains functions for building and solving CapATL formula trees
using bottom-up evaluation with knowledge-based reasoning.
"""

from typing import Any, Optional

from model_checker.algorithms.explicit.CapATL.knowledge import Node_PK
from model_checker.algorithms.explicit.CapATL.operators import (
    handle_and,
    handle_eventually,
    handle_globally,
    handle_next,
    handle_not,
    handle_or,
    handle_until,
)
from model_checker.algorithms.explicit.CapATL.utils import (
    X_agt_cap2,
    pointed_knowledge_set,
    verify_digits_and_letters,
)
from model_checker.algorithms.explicit.shared.atom_utils import (
    resolve_atom_with_constants,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import CapCGSProtocol


def _get_parser():
    return FormulaParserFactory.get_parser_instance("CapATL")


def _extract_coalition(val_str):
    """Extract coalition from CapATL formula operator string.

    CapATL uses format <{agents},bound>Op, e.g., <{1,2},3>F
    This extracts just the coalition part: {1,2}
    """
    start = val_str.find("{")
    end = val_str.find("}")
    return val_str[start : end + 1]


def build_tree(cgs: CapCGSProtocol, tpl: Any) -> Optional[Node_PK]:
    """
    Build CapATL formula tree from parsed formula tuple.

    Handles both atomic propositions and capacity constraints (e.g., "1c").
    Leaf nodes contain pointed knowledge sets representing states where
    the atom/capacity holds.

    Args:
        cgs: CGS model instance
        tpl: Parsed formula tuple from parser

    Returns:
        Root Node_PK of the formula tree, or None if invalid
    """
    if isinstance(tpl, tuple):
        root = Node_PK(tpl[0])
        if len(tpl) > 1:
            root.left = build_tree(cgs, tpl[1])
            if root.left is None:
                return None
        if len(tpl) > 2:
            root.right = build_tree(cgs, tpl[2])
            if root.right is None:
                return None
    else:
        if isinstance(tpl, tuple) and len(tpl) == 2:
            agent_str, prop_str = str(tpl[0]), str(tpl[1])
            if agent_str.isdigit() and prop_str and prop_str[0].islower():
                states_set = resolve_atom_with_constants(cgs, prop_str, _get_parser())
                if states_set is None:
                    return None
                Theta = pointed_knowledge_set(cgs)
                winning_pk = {
                    theta for theta in Theta if str(theta.state) in states_set
                }
                return Node_PK(winning_pk)
        tpl_str = str(tpl)
        if verify_digits_and_letters(tpl_str):
            # Atomic capacity constraint (e.g. 1c)
            ag_str = "".join(filter(str.isdigit, tpl_str))
            if not ag_str:
                return None
            ag_idx = int(ag_str) - 1
            cap_a = tpl_str[len(ag_str) :]

            all_cap_combos = X_agt_cap2(cgs)
            winning_combos = {
                c for c in all_cap_combos if ag_idx < len(c) and c[ag_idx] == cap_a
            }
            if not winning_combos:
                return None
            return Node_PK(winning_combos)
        else:
            # Atomic proposition
            states_set = resolve_atom_with_constants(cgs, tpl_str, _get_parser())
            if states_set is None:
                return None
            Theta = pointed_knowledge_set(cgs)
            winning_pk = {theta for theta in Theta if str(theta.state) in states_set}
            return Node_PK(winning_pk)

    return root


def solve_tree(cgs: CapCGSProtocol, node: Optional[Node_PK]) -> None:
    """
    Recursively solve the CapATL formula tree using bottom-up evaluation.

    Formula is parsed into a binary tree by the parser. Leaf nodes contain
    atomic propositions or capacity constraints (already resolved to pointed
    knowledge sets). Internal nodes apply CapATL operators to combine child
    results. Each node's value becomes the set of pointed knowledge elements
    where that subformula holds.

    Args:
        cgs: The CGS model instance
        node: Current tree node to evaluate
    """
    if node is None:
        return set()

    if node.left:
        solve_tree(cgs, node.left)
    if node.right:
        solve_tree(cgs, node.right)

    # Handle unary operators
    if node.right is None:
        val_str = str(node.value)
        if node.left is None:
            # Leaf node (atom or capacity)
            return node.value

        if _get_parser().verify("NOT", val_str):
            handle_not(cgs, node)

        elif _get_parser().verify("NEXT", val_str):
            coal_str = _extract_coalition(val_str)
            handle_next(cgs, node, coal_str)

        elif _get_parser().verify("EVENTUALLY", val_str):
            coal_str = _extract_coalition(val_str)
            handle_eventually(cgs, node, coal_str)

        elif _get_parser().verify("GLOBALLY", val_str):
            coal_str = _extract_coalition(val_str)
            handle_globally(cgs, node, coal_str)

    # Handle binary operators
    elif node.left and node.right:
        val_str = str(node.value)
        if _get_parser().verify("AND", val_str):
            handle_and(cgs, node)
        elif _get_parser().verify("OR", val_str):
            handle_or(cgs, node)
        elif _get_parser().verify("UNTIL", val_str):
            coal_str = _extract_coalition(val_str)
            handle_until(cgs, node, coal_str)

    return node.value
