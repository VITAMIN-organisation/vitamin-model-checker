"""LTL parser (PLY-based).

What it handles:
- LTL formulas with temporal operators (X, F, G, U) and boolean connectives.
- Propositions matching [a-z][a-z0-9_]*.
"""

import re
from typing import Optional

from ..parser_utils import run_common_prechecks
from ..shared_parser import BaseLogicParser


class LTLParser(BaseLogicParser):
    """Parser for LTL formulas (temporal operators X, F, G, U and boolean connectives).

    Use parse(formula) to get an AST tuple or None on invalid input.
    """

    def __init__(self):
        """Initialize the LTL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(["PROP"])
        self.build()

    t_PROP = r"[a-z][a-z0-9_]*"

    # --- Grammar Rules ---

    def p_expression_until(self, p):
        "expression : expression UNTIL expression"
        p[0] = ("U", p[1], p[3])

    def p_expression_unary_temporal(self, p):
        """expression : NEXT expression
        | GLOBALLY expression
        | EVENTUALLY expression"""
        p[0] = (p[1], p[2])

    # --- Validation ---

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allowed_uppercase={"X", "G", "F", "U", "R", "W"},
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False

        _VALID_OPERATORS = {
            "U",
            "G",
            "F",
            "X",
            "!",
            "&&",
            "||",
            "->",
            "AND",
            "OR",
            "NOT",
            "IMPLIES",
            "UNTIL",
            "GLOBALLY",
            "NEXT",
            "EVENTUALLY",
        }

        def validate_result(r):
            if isinstance(r, str):
                if r in _VALID_OPERATORS or r.upper() in _VALID_OPERATORS:
                    return True
                if not re.match(r"^[a-z][a-z0-9_]*$", r):
                    return False
            elif isinstance(r, tuple):
                for item in r:
                    if not validate_result(item):
                        return False
            return True

        return validate_result(result)
