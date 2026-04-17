"""RBATL parser (PLY-based).

Supported:
- Resource-bounded ATL with coalition-bound operators like `<1,2><5>F p` and `<1><3>G p`.
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, R, W, G, X, F).

Rejects:
- Coalitions missing a bound (e.g., `<1>F p`).
- Invalid or out-of-range coalition members relative to n_agent.
- Non-ASCII, null bytes, or disallowed special characters.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    validate_coalition_bound_token,
    verify_token,
)
from ..shared_parser import BaseLogicParser


class RBATLParser(BaseLogicParser):
    """Parser for RBATL formulas (coalition-bound operators and temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the RBATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            [
                "COALITION_BOUND",
                "PROP",
                "UNTIL",
                "RELEASE",
                "WEAK",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.max_coalition = 100
        self.bound_limit = 1_000_000
        self.build()

    t_PROP = r"[a-z][a-z0-9_]*"
    t_COALITION_BOUND = r"<\d+(?:,\d+)*><\d+(?:,\d+)*>"

    def t_RELEASE(self, t):
        r"R|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W|weak\b"
        t.value = "W"
        return t

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_BOUND expression UNTIL expression
        | COALITION_BOUND expression WEAK expression
        | COALITION_BOUND expression RELEASE expression"""
        coalition_bound_str = p[1]
        self._validate_coalition_bound(coalition_bound_str)
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION_BOUND GLOBALLY expression
        | COALITION_BOUND NEXT expression
        | COALITION_BOUND EVENTUALLY expression"""
        coalition_bound_str = p[1]
        self._validate_coalition_bound(coalition_bound_str)
        p[0] = (p[1] + p[2], p[3])

    def _validate_coalition_bound(self, coalition_bound_str):
        """Validate coalition/bound part to prevent malformed tokens."""
        return validate_coalition_bound_token(
            coalition_bound_str, self.max_coalition, bound_limit=self.bound_limit
        )

    # === Validation ===

    def parse(self, formula, n_agent=100, max_bound=None, **kwargs):
        self.max_coalition = n_agent
        if max_bound is not None:
            self.bound_limit = max_bound

        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        _ALLOWED_UPPERCASE = {"F", "G", "X", "U", "R", "W"}
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=True,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_uppercase=_ALLOWED_UPPERCASE,
            allowed_operators=None,
        )
        if not valid:
            return False, err

        if re.search(r"<\d+(?:,\d+)*>\s*[FGXURW]", formula) and not re.search(
            r"<\d+(?:,\d+)*><\d+(?:,\d+)*>", formula
        ):
            return (
                False,
                "RBATL requires a resource bound (e.g., <1><5>) for temporal operators",
            )
        return True, None

    def verify(self, token_name, string):
        return verify_token(self.lexer, token_name, string)
