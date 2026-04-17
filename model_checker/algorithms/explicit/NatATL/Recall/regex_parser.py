"""
Regex parser utilities for NatATL Recall.

This module provides utilities for distinguishing between regex patterns and
boolean formulas, and for checking if propositions hold in label rows.
"""

import re
from typing import List

from model_checker.parsers.game_structures.cgs import CGS


def is_regex_or_boolean_formula(pattern: str) -> str:
    """
    Determine if a pattern is a regex expression or boolean formula.

    Checks for regex special characters (*, +, ?, ., etc.) to distinguish
    between regex patterns (used for history-based conditions) and boolean
    formulas (used for state-based conditions).

    Args:
        pattern: Pattern string to classify

    Returns:
        "Regex" if pattern contains regex special characters,
        "Boolean Formula" otherwise

    Example:
        is_regex_or_boolean_formula("a and b") -> "Boolean Formula"
        is_regex_or_boolean_formula("a.b*") -> "Regex"
    """
    regex_special_chars = r"[*+?.()|{}[\]]"
    if re.search(regex_special_chars, pattern):
        return "Regex"
    return "Boolean Formula"


def check_prop_holds_in_label_row(cgs: CGS, prop: str, prop_matrix: List[int]) -> bool:
    """
    Check if a proposition (or compound proposition) holds in a label row.

    Evaluates propositional formulas recursively, supporting:
    - Atomic propositions (e.g., "p", "q")
    - Conjunction ("and")
    - Disjunction ("or")
    - Negation ("!" prefix)

    Args:
        cgs: CGS model object
        prop: Proposition string (may be compound, e.g., "a and b")
        prop_matrix: Label row (list of 0/1 values for each proposition)

    Returns:
        True if the proposition holds in the label row, False otherwise

    Example:
        check_prop_holds_in_label_row(cgs, "a and b", [1, 1, 0]) -> True
        check_prop_holds_in_label_row(cgs, "a or c", [1, 0, 0]) -> True
    """

    def eval_prop(prop_str: str) -> bool:
        """Recursively evaluate propositional formula."""
        prop_str = prop_str.strip()

        if re.search(r"\band\b", prop_str):
            sub_props = re.split(r"\band\b", prop_str)
            return all(eval_prop(sub_prop.strip()) for sub_prop in sub_props)
        elif re.search(r"\bor\b", prop_str):
            sub_props = re.split(r"\bor\b", prop_str)
            return any(eval_prop(sub_prop.strip()) for sub_prop in sub_props)
        elif prop_str.startswith("!"):
            return not eval_prop(prop_str[1:].strip())
        else:
            index = cgs.get_atom_index(prop_str)
            if index is None:
                return False
            if index >= len(prop_matrix):
                return False
            return prop_matrix[index] == 1

    return eval_prop(prop)
