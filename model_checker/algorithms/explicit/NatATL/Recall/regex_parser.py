"""For NatATL Recall: tell regex patterns from boolean formulas, and check
propositions in label rows."""

import re

from model_checker.parsers.game_structures.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index


def is_regex_or_boolean_formula(pattern: str) -> str:
    """Return "Regex" for a history condition, which holds a regex character such as
    `*`, `+`, `?` or `.` (`a.b*`), and "Boolean Formula" for a state condition
    (`a and b`)."""
    regex_special_chars = r"[*+?.()|{}[\]]"
    if re.search(regex_special_chars, pattern):
        return "Regex"
    return "Boolean Formula"


def check_prop_holds_in_label_row(cgs: CGS, prop: str, prop_matrix: list[int]) -> bool:
    """Whether `prop` (an atom, a `!` prefix, `and`, `or`) holds in `prop_matrix`, the
    0/1 label row of one state: `"a and b"` holds in `[1, 1, 0]`."""

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
            index = proposition_index(cgs.atomic_propositions, prop_str)
            if index is None:
                return False
            if index >= len(prop_matrix):
                return False
            return prop_matrix[index] == 1

    return eval_prop(prop)
