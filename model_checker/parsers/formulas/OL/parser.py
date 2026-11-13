"""OL parser (PLY): demonic cost prefix `<J2>` before U, R, W, G, X and F.

The prefix is required, so `F p` is rejected. Its budget is any natural number,
0 included, as in ECAI 2023 ("n is any number in N0").
"""

from model_checker.parsers.syntax_patterns import (
    OL_DEMONIC_LEADING_ZERO_RE,
    OL_DEMONIC_TOKEN,
)

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    demonic_leading_zero_error,
    run_common_prechecks,
    until_operands,
)
from ..shared_parser import BaseLogicParser, word_rule


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

    t_RELEASE = word_rule("RELEASE")
    t_WEAK = word_rule("WEAK")

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
        leading_zero = demonic_leading_zero_error(formula, OL_DEMONIC_LEADING_ZERO_RE)
        if leading_zero:
            return False, leading_zero
        return run_common_prechecks(
            formula,
            allow_hash_at=True,
            coalition_required=False,
            extra_invalid_regexes=(
                r"<J>(?!\d)",  # missing cost after J
                r"<(?!J)\d+>",  # numeric-only prefix without J
            ),
        )
