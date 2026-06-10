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
    X_agt_cap,
    pointed_knowledge_set,
    verify_digits_and_letters,
)
from model_checker.algorithms.explicit.shared.atom_utils import (
    resolve_atom_with_constants,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import CapCGSProtocol


def _extract_coalition(val_str):
    """Extract coalition from CapATL formula operator string.

    CapATL uses format <{agents},bound>Op, e.g., <{1,2},3>F
    This extracts just the coalition part: {1,2}
    """
    start = val_str.find("{")
    end = val_str.find("}")
    return val_str[start : end + 1]


def build_tree(cgs: CapCGSProtocol, tpl: Any) -> Optional[Node_PK]:
    """Build the CapATL formula tree from a parsed formula tuple."""
    parser = FormulaParserFactory.get_parser_instance("CapATL")
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
                states_set = resolve_atom_with_constants(cgs, prop_str, parser)
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

            all_cap_combos = {tuple(elem) for elem in X_agt_cap(cgs)}
            winning_combos = {
                c for c in all_cap_combos if ag_idx < len(c) and c[ag_idx] == cap_a
            }
            if not winning_combos:
                return None
            return Node_PK(winning_combos)
        else:
            # Atomic proposition
            states_set = resolve_atom_with_constants(cgs, tpl_str, parser)
            if states_set is None:
                return None
            Theta = pointed_knowledge_set(cgs)
            winning_pk = {theta for theta in Theta if str(theta.state) in states_set}
            return Node_PK(winning_pk)

    return root


def solve_tree(cgs: CapCGSProtocol, node: Optional[Node_PK]) -> None:
    """Evaluate the CapATL formula tree bottom-up."""
    if node is None:
        return set()

    if node.left:
        solve_tree(cgs, node.left)
    if node.right:
        solve_tree(cgs, node.right)

    parser = FormulaParserFactory.get_parser_instance("CapATL")

    if node.right is None:
        val_str = str(node.value)
        if node.left is None:
            return node.value

        if parser.verify("NOT", val_str):
            handle_not(cgs, node)

        elif parser.verify("NEXT", val_str):
            coal_str = _extract_coalition(val_str)
            handle_next(cgs, node, coal_str)

        elif parser.verify("EVENTUALLY", val_str):
            coal_str = _extract_coalition(val_str)
            handle_eventually(cgs, node, coal_str)

        elif parser.verify("GLOBALLY", val_str):
            coal_str = _extract_coalition(val_str)
            handle_globally(cgs, node, coal_str)

    elif node.left and node.right:
        val_str = str(node.value)
        if parser.verify("AND", val_str):
            handle_and(cgs, node)
        elif parser.verify("OR", val_str):
            handle_or(cgs, node)
        elif parser.verify("UNTIL", val_str):
            coal_str = _extract_coalition(val_str)
            handle_until(cgs, node, coal_str)

    return node.value
