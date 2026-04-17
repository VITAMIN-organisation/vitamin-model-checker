"""ATL parser (PLY-based).

What it handles:
- ATL formulas with coalition-prefixed temporal operators (U, G, X, F) and boolean connectives.
- Coalition syntax `<1,2>` with agent indices in [1, n_agent].
- Symbolic boolean operators `&&`, `||`, `!`, `->` and lowercase keywords
  `and`, `or`, `not`, `implies`.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    validate_ast,
    validate_coalition,
)
from ..shared_parser import BaseLogicParser


class ATLParser(BaseLogicParser):
    """Parser for ATL formulas (coalition-prefixed temporal operators and boolean connectives).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing if coalition validation is required.
    """

    def __init__(self):
        """Initialize the ATL lexer and parser (PLY)."""
        super().__init__()
        # Add ATL specific tokens
        self.tokens.extend(["COALITION", "PROP"])
        self.n_agent = 0
        self.build()

    def verify(self, token_name, string):
        """
        Verify if a token exists in the string (case-insensitive for ATL).
        """
        from ..parser_utils import verify_token

        return verify_token(self.lexer, token_name, string, case_sensitive=False)

    # --- ATL Specific Tokens ---
    t_COALITION = r"<\d+(?:,\d+)*>"
    t_PROP = r"[a-z][a-z\d_]*"

    # --- Grammar Rules ---
    # Binary boolean operators are inherited from BaseLogicParser

    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION LPAREN expression UNTIL expression RPAREN"""
        coalition_str = p[1]
        validate_coalition(coalition_str, self.n_agent)
        # Handle both forms: <coalition>expr1 U expr2 and <coalition>(expr1 U expr2)
        if len(p) == 5:
            p[0] = (p[1] + p[3], p[2], p[4])
        else:
            p[0] = (p[1] + p[4], p[3], p[5])

    def p_expression_unary(self, p):
        """expression : COALITION GLOBALLY expression
        | COALITION NEXT expression
        | COALITION EVENTUALLY expression"""
        coalition_str = p[1]
        validate_coalition(coalition_str, self.n_agent)
        p[0] = (p[1] + p[2], p[3])

    # --- Validation and Overrides ---

    def parse(self, formula, n_agent=0, **kwargs):
        self.n_agent = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        _ALLOWED_UPPERCASE_CHARS = {"U", "G", "X", "F"}

        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_uppercase=_ALLOWED_UPPERCASE_CHARS,
            allowed_operators=None,
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False

        _VALID_OPERATORS = {
            "U",
            "G",
            "X",
            "F",
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
            "!",
        }

        _COALITION_OPERATOR_PATTERN = re.compile(
            r"^<\d+(?:,\d+)*>(U|G|X|F|UNTIL|GLOBALLY|NEXT|EVENTUALLY)$",
            re.IGNORECASE,
        )

        try:
            if not validate_ast(
                result,
                _VALID_OPERATORS,
                coalition_pattern=_COALITION_OPERATOR_PATTERN,
            ):
                return False
        except Exception:
            return False

        return True

    def p_error(self, p):
        super().p_error(p)
