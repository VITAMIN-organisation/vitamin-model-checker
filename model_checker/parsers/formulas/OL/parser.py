"""OL parser (PLY-based).

Supported:
- OL formulas with demonic cost prefixes like `<J1>F p`, `<J2>G p`.
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, R, W, G, X, F).

Rejects:
- Missing or malformed demonic costs (e.g., `<J>F p`, `<J0>F p`, `<1>F p`).
- Empty formulas, non-ASCII, nulls, or disallowed special characters.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    verify_token,
)
from ..shared_parser import BaseLogicParser


class DemonicValueError(Exception):
    pass


class OLParser(BaseLogicParser):
    """Parser for OL formulas (demonic cost prefixes and temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    """

    def __init__(self):
        """Initialize the OL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            [
                "DEMONIC",
                "PROP",
                "UNTIL",
                "RELEASE",
                "WEAK",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.build()

    # === Tokens ===
    t_PROP = r"[a-z][a-z0-9_]*"
    t_DEMONIC = r"<J[1-9]\d*>"

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
        """expression : DEMONIC expression UNTIL expression
        | DEMONIC expression WEAK expression
        | DEMONIC expression RELEASE expression"""
        demonic_str = p[1]
        self._validate_demonic(demonic_str)
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : DEMONIC GLOBALLY expression
        | DEMONIC NEXT expression
        | DEMONIC EVENTUALLY expression"""
        demonic_str = p[1]
        self._validate_demonic(demonic_str)
        p[0] = (p[1] + p[2], p[3])

    def _validate_demonic(self, demonic_str):
        """Validate and extract cost value from demonic token like <J5>."""
        match = re.match(r"<J([1-9]\d*)>", demonic_str)
        if not match:
            raise DemonicValueError(f"Invalid demonic token: {demonic_str}")
        return match.group(1)

    # === Validation ===

    def parse(self, formula, **kwargs):
        try:
            return super().parse(formula, **kwargs)
        except DemonicValueError:
            return None

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        return run_common_prechecks(
            formula,
            allow_hash_at=True,
            coalition_required=False,
            allowed_uppercase={"F", "G", "X", "U", "R", "W", "J"},
            extra_invalid_regexes=(
                r"<J0>",  # zero cost
                r"<J>(?!\d)",  # missing cost
                r"(?<!J)<\d+>",  # numeric coalition without J prefix
            ),
        )

    def verify(self, token_name, string):
        return verify_token(self.lexer, token_name, string)
