"""CTL parser (PLY): path quantifiers A and E over the operators X, F, G and U.

Square brackets appear only in `A[p U q]` (Clarke, Emerson, Sistla 1986, p. 246).
"""

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_ctl_path_quantifiers,
)
from ..shared_parser import BaseLogicParser, quantifier_rules


class CTLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

    def __init__(self):
        """Initialize the CTL lexer and parser (PLY)."""
        super().__init__()
        # Add CTL specific tokens
        self.tokens.extend(["LBRACKET", "RBRACKET", "FORALL", "EXIST", "PROP"])
        self.build()

    # --- CTL Specific Tokens ---
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_PROP = PROPOSITION_TOKEN_PATTERN

    t_FORALL, t_EXIST = quantifier_rules("FGXU")

    # --- Grammar Rules ---

    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL LPAREN expression UNTIL expression RPAREN
        | EXIST LPAREN expression UNTIL expression RPAREN
        | FORALL LBRACKET expression UNTIL expression RBRACKET
        | EXIST LBRACKET expression UNTIL expression RBRACKET"""
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL NEXT expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST NEXT expression
        | EXIST EVENTUALLY expression"""
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # --- Validation ---

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            coalition_required=False,
            allow_hash_at=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),[]!&|->"),
        )
        if not valid:
            return False, err

        return validate_ctl_path_quantifiers(formula)
