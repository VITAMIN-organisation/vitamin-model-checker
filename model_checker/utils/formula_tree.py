"""Binary tree nodes for parsed logic formulas."""

from collections.abc import Callable
from typing import Any


class FormulaTreeNode:
    """Binary tree node with a value and optional left/right children."""

    def __init__(self, value: Any) -> None:
        self.value = value
        self.left: FormulaTreeNode | None = None
        self.right: FormulaTreeNode | None = None


def build_formula_tree(tpl: Any, atom_resolver: Callable[[Any], str | None]):
    """Build a formula tree from a parsed tuple; atom_resolver fills leaf values."""
    if isinstance(tpl, tuple):
        root = FormulaTreeNode(tpl[0])
        if len(tpl) > 1:
            left_child = build_formula_tree(tpl[1], atom_resolver)
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_formula_tree(tpl[2], atom_resolver)
                if right_child is None:
                    return None
                root.right = right_child
    else:
        leaf_value = atom_resolver(tpl)
        if leaf_value is None:
            return None
        if isinstance(leaf_value, set):
            leaf_value = str(tuple(sorted(leaf_value)))
        root = FormulaTreeNode(leaf_value)

    return root
