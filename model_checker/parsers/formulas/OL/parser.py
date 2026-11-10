"""OL parser (PLY): demonic cost prefix `<J2>` before U, R, W, G, X and F.

The prefix is required, so `F p` is rejected. Its budget is any natural number,
0 included, as in ECAI 2023 ("n is any number in N0").
"""

import re

from model_checker.parsers.syntax_patterns import OL_DEMONIC_TOKEN

from ..parser_utils import (
    BOOLEAN_AST_OPERATORS,
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_ast,
)
from ..shared_parser import BaseLogicParser

_LEADING_ZERO_BOUND_RE = re.compile(r"<J(0\d+)>")
_OL_MODAL_OPS = r"F|G|X|U|R|W|UNTIL|RELEASE|WEAK|NEXT|EVENTUALLY|GLOBALLY"
_OL_DEMONIC_OPERATOR_PATTERN = re.compile(
    rf"^{OL_DEMONIC_TOKEN}({_OL_MODAL_OPS})$",
    re.IGNORECASE,
)
_OL_VALID_OPERATORS = (
    frozenset(
        {
            "U",
            "R",
            "W",
            "X",
            "F",
            "G",
            "UNTIL",
            "RELEASE",
            "WEAK",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
        }
    )
    | BOOLEAN_AST_OPERATORS
)


class OLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

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
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W(?![a-zA-Z0-9_])|weak\b"
        t.value = "W"
        return t

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : DEMONIC expression UNTIL expression
        | DEMONIC expression WEAK expression
        | DEMONIC expression RELEASE expression
        | DEMONIC LPAREN expression UNTIL expression RPAREN
        | DEMONIC LPAREN expression WEAK expression RPAREN
        | DEMONIC LPAREN expression RELEASE expression RPAREN"""
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : DEMONIC GLOBALLY expression
        | DEMONIC NEXT expression
        | DEMONIC EVENTUALLY expression"""
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # === Validation ===

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        leading_zero = _LEADING_ZERO_BOUND_RE.search(formula)
        if leading_zero:
            return (
                False,
                f"Bound '{leading_zero.group(0)}' has a leading zero; write "
                f"<J{int(leading_zero.group(1))}>",
            )
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
