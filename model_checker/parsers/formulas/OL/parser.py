"""OL parser (PLY-based).

Supported:
- OL formulas with demonic cost prefixes like `<J1>F p`, `<J2>G p`.
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, R, W, G, X, F).

Rejects:
- Numeric-only prefixes (e.g. `<5>F p`) and bare temporal operators (e.g. `F p`).
- Missing or malformed demonic costs (e.g., `<J>F p`, `<J0>F p`).
- Empty formulas, non-ASCII, nulls, or disallowed special characters.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re

from model_checker.parsers.syntax_patterns import (
    OL_DEMONIC_BOUND_FULL_RE,
    OL_DEMONIC_TOKEN,
)

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    verify_token,
)
from ..shared_parser import BaseLogicParser

_OL_DEMONIC_OPERATOR_PATTERN = re.compile(
    r"^<J[1-9]\d*>(F|G|X|U|R|W|UNTIL|RELEASE|WEAK|NEXT|EVENTUALLY|GLOBALLY)$",
    re.IGNORECASE,
)
_OL_VALID_OPERATORS = frozenset(
    {
        "U",
        "R",
        "W",
        "X",
        "F",
        "G",
        "&&",
        "AND",
        "NOT",
        "UNTIL",
        "RELEASE",
        "WEAK",
        "NEXT",
        "EVENTUALLY",
        "GLOBALLY",
        "!",
        "->",
    }
)


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
    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_DEMONIC = OL_DEMONIC_TOKEN

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
        match = OL_DEMONIC_BOUND_FULL_RE.match(demonic_str)
        if not match:
            raise DemonicValueError(f"Invalid demonic token: {demonic_str}")
        cost = int(match.group(1))
        if cost < 1:
            raise DemonicValueError(
                f"Demonic cost must be a positive integer, got <J{cost}>"
            )
        return str(cost)

    # === Validation ===

    def parse(self, formula, **kwargs):
        try:
            return super().parse(formula, **kwargs)
        except DemonicValueError:
            return None

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=True,
            coalition_required=False,
            extra_invalid_regexes=(
                r"<J>(?!\d)",  # missing cost after J
                r"<(?!J)\d+>",  # numeric-only prefix without J
            ),
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(
            result,
            _OL_VALID_OPERATORS,
            coalition_pattern=_OL_DEMONIC_OPERATOR_PATTERN,
        )

    def verify(self, token_name, string):
        return verify_token(self.lexer, token_name, string)
