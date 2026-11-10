"""CapATL formula tree builder and bottom-up solver with knowledge-based reasoning."""

from typing import Any

from model_checker.algorithms.explicit.CapATL.knowledge import Node_PK
from model_checker.algorithms.explicit.CapATL.operators import (
    handle_and,
    handle_eventually,
    handle_globally,
    handle_implies,
    handle_next,
    handle_not,
    handle_or,
    handle_release,
    handle_until,
)
from model_checker.algorithms.explicit.CapATL.utils import pointed_knowledge_set
from model_checker.algorithms.explicit.shared.atom_utils import (
    resolve_atom_with_constants,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import CapCGSProtocol


def _extract_coalition(val_str):
    """Extract coalition set from CapATL operator string, e.g. <{1,2}>F -> {1,2}."""
    start = val_str.find("{")
    end = val_str.find("}")
    return val_str[start : end + 1]


def build_tree(cgs: CapCGSProtocol, tpl: Any, parser=None) -> Node_PK | None:
    """Build the CapATL formula tree from a parsed formula tuple."""
    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("CapATL")
    if isinstance(tpl, tuple):
        root = Node_PK(tpl[0])
        if len(tpl) > 1:
            root.left = build_tree(cgs, tpl[1], parser)
            if root.left is None:
                return None
        if len(tpl) > 2:
            root.right = build_tree(cgs, tpl[2], parser)
            if root.right is None:
                return None
        return root

    # Atomic proposition: capacities appear only as `a is c` inside K, which the
    # solver does not evaluate, so every leaf is a proposition name.
    states_set = resolve_atom_with_constants(cgs, str(tpl), parser)
    if states_set is None:
        return None
    Theta = pointed_knowledge_set(cgs)
    winning_pk = {theta for theta in Theta if str(theta.state) in states_set}
    return Node_PK(winning_pk)


def solve_tree(cgs: CapCGSProtocol, node: Node_PK | None, parser=None) -> None:
    """Evaluate the CapATL formula tree bottom-up."""
    if node is None:
        return

    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("CapATL")

    if node.left:
        solve_tree(cgs, node.left, parser)
    if node.right:
        solve_tree(cgs, node.right, parser)

    if node.right is None:
        val_str = str(node.value)
        if node.left is None:
            return

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
        elif parser.verify("IMPLIES", val_str):
            handle_implies(cgs, node)
        elif parser.verify("UNTIL", val_str):
            coal_str = _extract_coalition(val_str)
            handle_until(cgs, node, coal_str)
        elif parser.verify("RELEASE", val_str):
            coal_str = _extract_coalition(val_str)
            handle_release(cgs, node, coal_str)
